"""DMP_ExtLoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.5."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadEvent, LoadState, ResourceGenericPropertyId
from xknx.telegram import apci

from .const import LOAD_STATE_POLL_INTERVAL, LOAD_STATE_TRANSITION_TIMEOUT
from .dmp_ext_load_state_machine_read_r_co_io import (
    dmp_ext_load_state_machine_read_r_co_io,
    ext_state_response_load_state,
)
from .load_state_machine import (
    await_expected_state,
    check_poll_interval,
    load_control_data,
)

__all__ = ["dmp_ext_load_state_machine_write_r_co_io"]


async def dmp_ext_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    event: LoadEvent,
    event_data: bytes = b"",
    verify: bool = True,
    property_id: int = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
    timeout: float = LOAD_STATE_TRANSITION_TIMEOUT,
    poll_interval: float = LOAD_STATE_POLL_INTERVAL,
) -> LoadState:
    """
    Send an event to a Load State Machine with A_FunctionPropertyExtCommand.

    DMP_ExtLoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.31.5. The command has the format of
    DMP_LoadStateMachineWrite_RCo_IO (§3.31.3); the device answers with an
    A_FunctionPropertyExtState_Response carrying the resulting state.
    Requires an established connection (DM_Connect must be executed first).

    A device may go offline during the intermediate state LoadCompleting (KNX
    v01.10.01 - Resources 03.05.01 - §4.23.2.3.2 and §4.23.2.4.1). The
    connection is lost then and ManagementConnectionTimeout is raised;
    re-establishing it is left to the caller.

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type hosting the Load State Machine
    :param object_instance: Instance of that Interface Object Type
    :param event: The Load Event
    :param event_data: Additional data of the event - e.g. the sub type and data
        of an Additional Load Control (§3.31.3.4), see
        load_event_relative_allocation and load_event_data_relative_allocation.
        At most 9 octets; filled up with 00h to the 10 octets of a load control.
    :param verify: Check the resulting state against the one `event` leads to
        (KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.3, Table 94), reading it
        again while the Load State Machine reports an optional intermediate
        state: LOAD_COMPLETING for every event, UNLOADING for Unload. A device
        still completing a previous load may ignore the event and end in LOADED,
        which fails the check for any event but Load Completed.
    :param property_id: Property of the Load State Machine
    :param timeout: Seconds to wait for an intermediate state to end - KNX
        v01.10.01 - Resources 03.05.01 - §4.23.2.1 makes 30 seconds the minimum
    :param poll_interval: Seconds between reads of an intermediate state, at
        most 3 - KNX v01.10.01 - Resources 03.05.01 - §4.23.2.4.1 limits the
        period to half the TL-timeout to keep the connection alive
    :return: The resulting Load State
    :raises ValueError: If event_data is longer than 9 octets or poll_interval
        longer than 3 seconds
    :raises VerificationError: If verify is enabled and the resulting state is
        not the expected one, or an intermediate state lasts longer than
        `timeout`
    :raises ManagementConnectionTimeout: If the device does not answer, e.g.
        while it is offline during LoadCompleting
    :raises ManagementConnectionError: If the device answers with a negative
        return code, no data or an unknown state
    """
    check_poll_interval(poll_interval)
    response = await conn.request(
        payload=apci.FunctionPropertyExtCommand(
            interface_object_type=object_type,
            object_instance=object_instance,
            property_id=property_id,
            data=load_control_data(event, event_data),
        ),
    )
    state = ext_state_response_load_state(response)
    if not verify:
        return state
    return await await_expected_state(
        state,
        event,
        lambda: dmp_ext_load_state_machine_read_r_co_io(
            conn, object_type, object_instance, property_id
        ),
        timeout,
        poll_interval,
    )
