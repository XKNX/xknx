"""DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import LoadEvent, LoadState, ResourceGenericPropertyId
from xknx.telegram import apci

from ._load_state_machine import (
    TRANSITION_TIMEOUT,
    await_expected_state,
    decode_load_state,
    load_control_data,
)
from .dmp_load_state_machine_read_r_io import dmp_load_state_machine_read_r_io

__all__ = ["dmp_load_state_machine_write_r_co_io"]


async def dmp_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    object_index: int,
    event: LoadEvent,
    event_data: bytes = b"",
    verify: bool = False,
    timeout: float = TRANSITION_TIMEOUT,
    poll_interval: float = 1.0,
) -> LoadState:
    """
    Send an event to a property based Load State Machine.

    DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.3. Writes the event to PID_LOAD_STATE_CONTROL of the
    Interface Object hosting the Load State Machine; the device answers with
    its resulting state. Requires an established connection (DM_Connect must be
    executed first).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the Interface Object hosting the Load State
        Machine
    :param event: The Load Event
    :param event_data: Additional data of the event - eg. the sub type and data
        of an Additional Load Control (§3.31.3.4). At most 9 octets; filled up
        with 00h to the 10 octets of a load control.
    :param verify: Check the resulting state against the one `event` leads to
        (KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.3, Table 94), reading it
        again while the Load State Machine reports the optional intermediate
        state UNLOADING or LOAD_COMPLETING
    :param timeout: Seconds to wait for an intermediate state to end - KNX
        v01.10.01 - Resources 03.05.01 - §4.23.2.1 makes 30 seconds the minimum
    :param poll_interval: Seconds between reads of an intermediate state
    :return: The resulting Load State
    :raises ValueError: If event_data is longer than 9 octets
    :raises VerificationError: If verify is enabled and the resulting state is
        not the expected one
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    response = await conn.request(
        payload=apci.PropertyValueWrite(
            object_index=object_index,
            property_id=ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
            count=1,
            start_index=1,
            data=load_control_data(event, event_data),
        ),
    )
    if response.payload.count == 0:
        raise ManagementConnectionError(
            f"Load State Machine write failed: object {object_index} returned "
            "nr_of_elem=0"
        )
    state = decode_load_state(response.payload.data)
    if not verify:
        return state
    return await await_expected_state(
        state,
        event,
        lambda: dmp_load_state_machine_read_r_io(conn, object_index),
        timeout,
        poll_interval,
    )
