"""DMP_LoadStateMachineWrite_RCo_Mem — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.2."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadEvent, LoadState, ResourceObjectType

from .const import LOAD_CONTROL_LENGTH, MEM_MANAGEMENT_CONTROL_ADDRESS
from .dmp_load_state_machine_read_r_co_mem import dmp_load_state_machine_read_r_co_mem
from .dmp_mem_write_r_co import dmp_mem_write_r_co
from .load_state_machine import EXPECTED_STATE, check_mem_state_machine, check_state

__all__ = ["dmp_load_state_machine_write_r_co_mem"]

# KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.2: the load state is
# read "until loadstate is correct (for max. 3 times)".
MAX_STATE_READS = 3


async def dmp_load_state_machine_write_r_co_mem(
    conn: P2PConnection,
    state_machine: ResourceObjectType,
    event: LoadEvent,
    event_data: bytes = b"",
    verify: bool = True,
) -> LoadState:
    """
    Send an event to a memory mapped Load State Machine.

    DMP_LoadStateMachineWrite_RCo_Mem — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.31.2. Only for mask version 070nh (BIM M112): writes the 11
    octet management control to 0104h - the state machine type and event in
    one octet, then the event data - and reads the resulting load state. The
    spec says this procedure "shall not be used for further developments of
    Management Servers". Requires an established connection (DM_Connect must
    be executed first).

    :param conn: Active P2P connection to the device
    :param state_machine: Type of the Load State Machine - OBJECT_ADDRESS_TABLE,
        OBJECT_ASSOCIATION_TABLE, OBJECT_APPLICATION_PROGRAM or
        OBJECT_INTERFACE_PROGRAM (PEI program)
    :param event: The Load Event
    :param event_data: The data following the state machine / event octet - e.g.
        segment type, segment ID and the allocation of an AllocAbsDataSeg
        event. At most 10 octets; filled up with 00h.
    :param verify: Read the load state up to 3 times until it is the one
        `event` leads to (KNX v01.10.01 - Resources 03.05.01 - §4.23.2.3.3,
        Table 94). Disabled, the state is read once.
    :return: The resulting Load State
    :raises ValueError: If state_machine is not one of the four types or
        event_data is longer than 10 octets
    :raises VerificationError: If verify is enabled and the expected state is
        not reached
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    check_mem_state_machine(state_machine)
    if len(event_data) > LOAD_CONTROL_LENGTH:
        raise ValueError(
            f"event_data must be at most {LOAD_CONTROL_LENGTH} octets, "
            f"got {len(event_data)}"
        )
    control = bytes([state_machine << 4 | event]) + event_data.ljust(
        LOAD_CONTROL_LENGTH, b"\x00"
    )
    await dmp_mem_write_r_co(conn, MEM_MANAGEMENT_CONTROL_ADDRESS, control)

    state = await dmp_load_state_machine_read_r_co_mem(conn, state_machine)
    expected = EXPECTED_STATE.get(event)
    if not verify or expected is None:
        return state
    for _ in range(MAX_STATE_READS - 1):
        if state == expected:
            return state
        state = await dmp_load_state_machine_read_r_co_mem(conn, state_machine)
    check_state(state, expected)
    return state
