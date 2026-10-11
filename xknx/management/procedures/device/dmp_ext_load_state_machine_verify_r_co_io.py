"""DMP_ExtLoadStateMachineVerify_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.4."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import LoadState, ResourceGenericPropertyId

from ._load_state_machine import check_state
from .dmp_ext_load_state_machine_read_r_co_io import (
    dmp_ext_load_state_machine_read_r_co_io,
)

__all__ = ["dmp_ext_load_state_machine_verify_r_co_io"]


async def dmp_ext_load_state_machine_verify_r_co_io(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    state: LoadState,
    property_id: int = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
) -> None:
    """
    Verify the state of a Load State Machine with A_FunctionPropertyExtState_Read.

    DMP_ExtLoadStateMachineVerify_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.32.4. Requires an established connection
    (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type hosting the Load State Machine
    :param object_instance: Instance of that Interface Object Type
    :param state: The expected Load State
    :param property_id: Property of the Load State Machine
    :raises VerificationError: If the Load State Machine is in another state
    :raises ManagementConnectionError: If the device answers with a negative
        return code, no data or an unknown state
    """
    check_state(
        await dmp_ext_load_state_machine_read_r_co_io(
            conn, object_type, object_instance, property_id
        ),
        state,
    )
