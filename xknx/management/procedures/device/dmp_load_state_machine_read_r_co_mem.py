"""DMP_LoadStateMachineRead_RCo_Mem — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.2."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadState, ResourceObjectType

from ._load_state_machine import decode_load_state, mem_load_state_address
from .dmp_mem_read_r_co import dmp_mem_read_r_co

__all__ = ["dmp_load_state_machine_read_r_co_mem"]


async def dmp_load_state_machine_read_r_co_mem(
    conn: P2PConnection, state_machine: ResourceObjectType
) -> LoadState:
    """
    Read the state of a memory mapped Load State Machine.

    DMP_LoadStateMachineRead_RCo_Mem — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.33.2. Only for mask version 070nh (BIM M112), which has one
    Load State Machine of each type at a fixed memory address. Requires an
    established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param state_machine: Type of the Load State Machine - OBJECT_ADDRESS_TABLE,
        OBJECT_ASSOCIATION_TABLE, OBJECT_APPLICATION_PROGRAM or
        OBJECT_INTERFACE_PROGRAM (PEI program)
    :return: The current Load State
    :raises ValueError: If state_machine is not one of the four types
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    address = mem_load_state_address(state_machine)
    return decode_load_state(await dmp_mem_read_r_co(conn, address, 1))
