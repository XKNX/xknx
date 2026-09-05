"""DMP_LoadStateMachineRead_R_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.3."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from .dmp_interface_object_read_r import dmp_interface_object_read_r
from .load_state import LoadState, decode_load_state

__all__ = ["dmp_load_state_machine_read_r_io"]


async def dmp_load_state_machine_read_r_io(
    conn: P2PConnection, object_index: int
) -> LoadState:
    """
    Read the current state of an interface object's Load State Machine.

    DMP_LoadStateMachineRead_R_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.33.3. Requires an established connection (DM_Connect must
    be executed first).

    The property carrying the Load State Machine (``PID_LOAD_STATE_CONTROL``)
    is always known by definition here, so the spec's optional
    ``A_PropertyDescription_Read`` step - "if Property... is unknown to the
    Management Client" - never applies, matching
    :func:`~.dmp_load_state_machine_write_r_co_io.dmp_load_state_machine_write_r_co_io`'s
    own reasoning for the same step.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :return: The current Load State
    :raises ManagementConnectionError: If the device reports an error reading
        the property, or the read Load State is not a valid state
    """
    data = await dmp_interface_object_read_r(
        conn,
        object_index,
        ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
        count=1,
        start_index=1,
    )
    return decode_load_state(data, f"object {object_index}")
