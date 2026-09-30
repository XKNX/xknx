"""DMP_ExtRunStateMachineRead_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.36.4."""

from __future__ import annotations

from functools import partial

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from ._state_machine import ext_context, ext_read_state
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
    returned. The response must echo the requested Interface Object Type,
    Object Instance and PID (MP §3.36.4), so a stale or mismatched response
    isn't decoded as this object's Run State.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :return: The current Run State
    :raises ManagementConnectionError: If the device returns a negative
        return code, the response doesn't echo the request, or the read
        Run State is not a valid state
    """
    return await ext_read_state(
        conn,
        interface_object_type,
        object_instance,
        ResourceGenericPropertyId.PID_RUN_STATE_CONTROL,
        partial(
            decode_run_state,
            context=ext_context(interface_object_type, object_instance),
        ),
        "Run State Machine",
    )
