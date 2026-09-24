"""DMP_ExtRunStateMachineRead_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.36.4."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId
from xknx.telegram import apci

from .run_state import RunState, decode_run_state

__all__ = ["dmp_ext_run_state_machine_read_r_co_io"]


async def dmp_ext_run_state_machine_read_r_co_io(
    conn: P2PConnection, interface_object_type: int, object_instance: int
) -> RunState:
    """
    Read the current state of an extended-addressed Run State Machine.

    DMP_ExtRunStateMachineRead_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.36.4. Addresses the interface object by
    Interface Object Type + Object Instance rather than the connection-local
    object index
    :func:`~.dmp_run_state_machine_read_r_io.dmp_run_state_machine_read_r_io`
    uses. Requires an established connection (DM_Connect must be executed
    first).

    Unlike ``A_FunctionPropertyExtCommand``'s own ``return_code`` (see
    :func:`~.dmp_ext_function_property_write_r.dmp_ext_function_property_write_r_conn`),
    ``PID_RUN_STATE_CONTROL`` is a ``PDT_CONTROL`` property, for which the
    Application Layer defines a fixed response shape (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.8.4): a positive ``return_code``
    always carries the 1 octet state, a negative one always carries none.
    So a negative ``return_code`` here is unambiguously an error, not a
    function-specific result to interpret - and is raised rather than
    returned.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :return: The current Run State
    :raises ManagementConnectionError: If the device returns a negative
        return code, or the read Run State is not a valid state
    """
    response = await conn.request(
        apci.FunctionPropertyExtStateRead(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=ResourceGenericPropertyId.PID_RUN_STATE_CONTROL,
        )
    )
    if response.payload.return_code != apci.ReturnCode.E_SUCCESS:
        raise ManagementConnectionError(
            f"interface object type {interface_object_type} instance "
            f"{object_instance} Run State Machine read failed: "
            f"{response.payload.return_code.name}"
        )
    return decode_run_state(
        response.payload.data,
        f"interface object type {interface_object_type} instance {object_instance}",
    )
