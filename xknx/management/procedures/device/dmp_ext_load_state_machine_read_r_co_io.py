"""DMP_ExtLoadStateMachineRead_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.4."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId
from xknx.telegram import apci

from ._pdt_control import check_ext_echo, pdt_control_state_data
from .load_state import LoadState, decode_load_state

__all__ = ["dmp_ext_load_state_machine_read_r_co_io"]


async def dmp_ext_load_state_machine_read_r_co_io(
    conn: P2PConnection, interface_object_type: int, object_instance: int
) -> LoadState:
    """
    Read the current state of an extended-addressed Load State Machine.

    DMP_ExtLoadStateMachineRead_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.33.4. Addresses the interface object by
    Interface Object Type + Object Instance rather than the connection-local
    object index
    :func:`~.dmp_load_state_machine_read_r_io.dmp_load_state_machine_read_r_io`
    uses. Requires an established connection (DM_Connect must be executed
    first).

    Unlike ``A_FunctionPropertyExtCommand``'s own ``return_code`` (see
    :func:`~.dmp_ext_function_property_write_r.dmp_ext_function_property_write_r_conn`),
    ``PID_LOAD_STATE_CONTROL`` is a ``PDT_CONTROL`` property, for which the
    Application Layer defines a fixed response shape (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.8.4): a positive ``return_code`` always
    carries the 1 octet state, a negative one always carries no data at all.
    So a negative ``return_code`` here is unambiguously an error, not a
    function-specific result to interpret - and is raised rather than
    returned. The response must echo the requested Interface Object Type,
    Object Instance and PID (MP §3.33.4), so a stale or mismatched response
    isn't decoded as this object's Load State.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :return: The current Load State
    :raises ManagementConnectionError: If the device returns a negative
        return code, the response doesn't echo the request, or the read Load
        State is not a valid state
    """
    property_id = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL
    response = await conn.request(
        apci.FunctionPropertyExtStateRead(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
        )
    )
    check_ext_echo(
        response.payload, interface_object_type, object_instance, property_id
    )
    context = (
        f"interface object type {interface_object_type} instance {object_instance}"
    )
    return decode_load_state(
        pdt_control_state_data(response.payload, f"{context} Load State Machine read"),
        context,
    )
