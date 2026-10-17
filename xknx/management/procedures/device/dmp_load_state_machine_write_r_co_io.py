"""DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import LoadEvent, LoadState, ResourceGenericPropertyId
from xknx.telegram import apci

from .const import LOAD_STATE_POLL_INTERVAL, LOAD_STATE_TRANSITION_TIMEOUT
from .dmp_load_state_machine_read_r_io import dmp_load_state_machine_read_r_io
from .load_state_machine import (
    await_expected_state,
    check_poll_interval,
    decode_load_state,
    load_control_data,
)

__all__ = [
    "dmp_load_state_machine_write_r_co_io",
    "load_event_data_relative_allocation",
    "load_event_relative_allocation",
]

# Sub types of an Additional Load Control - KNX v02.01.02 - Management
# Procedures 03.05.02 - §3.31.3.4.
RELATIVE_ALLOCATION = 0x0A
DATA_RELATIVE_ALLOCATION = 0x0B


def load_event_relative_allocation(size: int) -> bytes:
    """
    Return the event data of a Load Event Relative Allocation.

    KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3.4: sub type 0Ah,
    then the maximum size of the loadable part in octets as 2 octets. It is
    sent as an Additional Load Control, e.g. in `additional_load_controls` of
    dmp_download_loadable_part_r_co_io.

    :param size: Maximum size of the loadable part in octets, 0..FFFFh
    :return: The event data, without the event and fill octets
    :raises ValueError: If size does not fit into 2 octets
    """
    if not 0 <= size <= 0xFFFF:
        raise ValueError(f"size must be 0..0xFFFF, got {size}")
    return bytes([RELATIVE_ALLOCATION]) + size.to_bytes(2, "big")


def load_event_data_relative_allocation(size: int, fill: int | None = None) -> bytes:
    """
    Return the event data of a Load Event Data Relative Allocation.

    KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3.4: sub type 0Bh,
    the requested memory size as 4 octets, the mode and the fill octet. Bit 0
    of the mode is set if `fill` is given, so the device fills the allocated
    memory with it; otherwise the memory contents stay unchanged. It is sent
    as an Additional Load Control, e.g. in `additional_load_controls` of
    dmp_download_loadable_part_r_co_io.

    :param size: Requested memory size in octets, 0..FFFFFFFFh
    :param fill: Value to fill the allocated memory with, 0..FFh
    :return: The event data, without the event and reserved octets
    :raises ValueError: If size does not fit into 4 octets or fill into 1 octet
    """
    if not 0 <= size <= 0xFFFFFFFF:
        raise ValueError(f"size must be 0..0xFFFFFFFF, got {size}")
    if fill is not None and not 0 <= fill <= 0xFF:
        raise ValueError(f"fill must be 0..0xFF, got {fill}")
    mode = 0 if fill is None else 1
    return (
        bytes([DATA_RELATIVE_ALLOCATION])
        + size.to_bytes(4, "big")
        + bytes([mode, fill or 0])
    )


async def dmp_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    object_index: int,
    event: LoadEvent,
    event_data: bytes = b"",
    verify: bool = True,
    property_id: int = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
    timeout: float = LOAD_STATE_TRANSITION_TIMEOUT,
    poll_interval: float = LOAD_STATE_POLL_INTERVAL,
) -> LoadState:
    """
    Send an event to a property based Load State Machine.

    DMP_LoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.3. Writes the event to the load state Property
    (PID_LOAD_STATE_CONTROL) of the Interface Object hosting the Load State
    Machine; the device answers with its resulting state. Requires an
    established connection (DM_Connect must be executed first).

    A device may go offline during the intermediate state LoadCompleting (KNX
    v01.10.01 - Resources 03.05.01 - §4.23.2.3.2 and §4.23.2.4.1). The
    connection is lost then and ManagementConnectionTimeout is raised;
    re-establishing it is left to the caller.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the Interface Object hosting the Load State
        Machine
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
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    check_poll_interval(poll_interval)
    response = await conn.request(
        payload=apci.PropertyValueWrite(
            object_index=object_index,
            property_id=property_id,
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
        lambda: dmp_load_state_machine_read_r_io(conn, object_index, property_id),
        timeout,
        poll_interval,
    )
