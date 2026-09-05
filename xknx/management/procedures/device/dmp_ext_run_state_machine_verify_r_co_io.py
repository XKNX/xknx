"""DMP_ExtRunStateMachineVerify_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.35.4."""

from __future__ import annotations

from xknx.exceptions import VerificationError
from xknx.management.management import P2PConnection

from .dmp_ext_run_state_machine_read_r_co_io import (
    dmp_ext_run_state_machine_read_r_co_io,
)
from .run_state import RunState

__all__ = ["dmp_ext_run_state_machine_verify_r_co_io"]


async def dmp_ext_run_state_machine_verify_r_co_io(
    conn: P2PConnection,
    interface_object_type: int,
    object_instance: int,
    expected_state: RunState,
) -> None:
    """
    Verify an extended-addressed Run State Machine is in the expected state.

    DMP_ExtRunStateMachineVerify_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.35.4. Addresses the interface object by
    Interface Object Type + Object Instance rather than the connection-local
    object index
    :func:`~.dmp_run_state_machine_verify_r_io.dmp_run_state_machine_verify_r_io`
    uses. Requires an established connection (DM_Connect must be executed
    first). Read-only - does not write anything first and does not retry.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :param expected_state: The Run State the device is expected to report
    :raises ManagementConnectionError: If the device returns a negative
        return code, or the read Run State is not a valid state
    :raises VerificationError: If the device's Run State doesn't match
        ``expected_state``
    """
    state = await dmp_ext_run_state_machine_read_r_co_io(
        conn, interface_object_type, object_instance
    )
    if state != expected_state:
        raise VerificationError(
            f"interface object type {interface_object_type} instance "
            f"{object_instance} Run State Machine verify failed: "
            f"expected {expected_state.name}, got {state.name}"
        )
