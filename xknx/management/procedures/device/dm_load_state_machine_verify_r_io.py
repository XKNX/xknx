"""DM_LoadStateMachineVerify_R_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.3."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadState, ResourceGenericPropertyId

from .dmp_load_state_machine_read_r_io import dmp_load_state_machine_read_r_io
from .load_state_machine import check_state

__all__ = ["dm_load_state_machine_verify_r_io"]


async def dm_load_state_machine_verify_r_io(
    conn: P2PConnection,
    object_index: int,
    state: LoadState,
    property_id: int = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
) -> None:
    """
    Verify the state of a property based Load State Machine.

    DM_LoadStateMachineVerify_R_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.32.3. Requires an established connection (DM_Connect must be
    executed first).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the Interface Object hosting the Load State
        Machine
    :param state: The expected Load State
    :param property_id: Property of the Load State Machine
    :raises VerificationError: If the Load State Machine is in another state
    :raises ManagementConnectionError: If the device returns no data or an
        unknown state
    """
    check_state(
        await dmp_load_state_machine_read_r_io(conn, object_index, property_id),
        state,
    )
