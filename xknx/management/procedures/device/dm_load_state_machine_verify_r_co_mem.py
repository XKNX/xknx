"""DM_LoadStateMachineVerify_RCo_Mem — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.2."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadState, ResourceObjectType

from .dmp_load_state_machine_read_r_co_mem import dmp_load_state_machine_read_r_co_mem
from .load_state_machine import check_state

__all__ = ["dm_load_state_machine_verify_r_co_mem"]


async def dm_load_state_machine_verify_r_co_mem(
    conn: P2PConnection, state_machine: ResourceObjectType, state: LoadState
) -> None:
    """
    Verify the state of a memory mapped Load State Machine.

    DM_LoadStateMachineVerify_RCo_Mem — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.32.2. Only for mask version 070nh (BIM M112). Requires an
    established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param state_machine: Type of the Load State Machine
    :param state: The expected Load State
    :raises ValueError: If state_machine is not one of the four types
    :raises VerificationError: If the Load State Machine is in another state
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    check_state(await dmp_load_state_machine_read_r_co_mem(conn, state_machine), state)
