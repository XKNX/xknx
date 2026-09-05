"""DMP_RunStateMachineVerify_R_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.35.3."""

from __future__ import annotations

from xknx.exceptions import VerificationError
from xknx.management.management import P2PConnection

from .dmp_run_state_machine_read_r_io import dmp_run_state_machine_read_r_io
from .run_state import RunState

__all__ = ["dmp_run_state_machine_verify_r_io"]


async def dmp_run_state_machine_verify_r_io(
    conn: P2PConnection, object_index: int, expected_state: RunState
) -> None:
    """
    Verify an interface object's Run State Machine is in the expected state.

    DMP_RunStateMachineVerify_R_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.35.3. Requires an established connection (DM_Connect must
    be executed first). Read-only - unlike
    :func:`~.dmp_run_state_machine_write_r_io.dmp_run_state_machine_write_r_io`'s
    own optional ``expected_state`` polling, this does not write anything
    first and does not retry. Delegates to
    :func:`~.dmp_run_state_machine_read_r_io.dmp_run_state_machine_read_r_io`,
    which - like the write procedure - skips the spec's optional
    ``A_PropertyDescription_Read`` step, since ``PID_RUN_STATE_CONTROL`` is
    always known by definition here.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param expected_state: The Run State the device is expected to report
    :raises ManagementConnectionError: If the device reports an error reading
        the property, or the read Run State is not a valid state
    :raises VerificationError: If the device's Run State doesn't match
        ``expected_state``
    """
    state = await dmp_run_state_machine_read_r_io(conn, object_index)
    if state != expected_state:
        raise VerificationError(
            f"object {object_index} Run State Machine verify failed: "
            f"expected {expected_state.name}, got {state.name}"
        )
