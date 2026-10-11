"""DMP_ExtLoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.5."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadEvent, LoadState, ResourceGenericPropertyId
from xknx.telegram import apci

from ._load_state_machine import (
    TRANSITION_TIMEOUT,
    await_expected_state,
    load_control_data,
)
from .dmp_ext_load_state_machine_read_r_co_io import (
    dmp_ext_load_state_machine_read_r_co_io,
    ext_state_response_load_state,
)

__all__ = ["dmp_ext_load_state_machine_write_r_co_io"]


async def dmp_ext_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    event: LoadEvent,
    event_data: bytes = b"",
    verify: bool = False,
    property_id: int = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
    timeout: float = TRANSITION_TIMEOUT,
    poll_interval: float = 1.0,
) -> LoadState:
    """
    Send an event to a Load State Machine with A_FunctionPropertyExtCommand.

    DMP_ExtLoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.31.5. The command has the format of
    DMP_LoadStateMachineWrite_RCo_IO (§3.31.3); the device answers with an
    A_FunctionPropertyExtState_Response carrying the resulting state.
    Requires an established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type hosting the Load State Machine
    :param object_instance: Instance of that Interface Object Type
    :param event: The Load Event
    :param event_data: Additional data of the event, at most 9 octets; filled
        up with 00h to the 10 octets of a load control
    :param verify: Check the resulting state against the one `event` leads to
        (KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.3, Table 94), reading it
        again while the Load State Machine reports the optional intermediate
        state UNLOADING or LOAD_COMPLETING
    :param property_id: Property of the Load State Machine
    :param timeout: Seconds to wait for an intermediate state to end - KNX
        v01.10.01 - Resources 03.05.01 - §4.23.2.1 makes 30 seconds the minimum
    :param poll_interval: Seconds between reads of an intermediate state
    :return: The resulting Load State
    :raises ValueError: If event_data is longer than 9 octets
    :raises VerificationError: If verify is enabled and the resulting state is
        not the expected one
    :raises ManagementConnectionError: If the device answers with a negative
        return code, no data or an unknown state
    """
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
