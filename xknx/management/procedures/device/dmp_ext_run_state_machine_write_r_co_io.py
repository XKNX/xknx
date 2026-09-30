"""DMP_ExtRunStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.34.4."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from ._pdt_control import pdt_control_state_data
from ._state_machine import check_event_size, ext_context
from .dmp_ext_function_property_write_r import dmp_ext_function_property_write_r_conn
from .run_state import RunState, decode_run_state

__all__ = ["dmp_ext_run_state_machine_write_r_co_io"]


async def dmp_ext_run_state_machine_write_r_co_io(
    conn: P2PConnection,
    interface_object_type: int,
    object_instance: int,
    event_data: bytes,
    *,
    max_apdu_length: int,
) -> RunState:
    """
    Write a run event to an extended-addressed Run State Machine.

    DMP_ExtRunStateMachineWrite_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.34.4. Addresses the interface object by
    Interface Object Type + Object Instance rather than the connection-local
    object index
    :func:`~.dmp_run_state_machine_write_r_io.dmp_run_state_machine_write_r_io`
    uses. The command format is identical to that procedure's - see
    :mod:`xknx.management.procedures.device.run_state` for builders such as
    :func:`~.run_state.restart` or :func:`~.run_state.stop`. Requires an
    established connection (DM_Connect must be executed first).

    Sent as ``A_FunctionPropertyExtCommand`` rather than
    ``A_PropertyValueExt_Write``. Unlike
    :func:`~.dmp_ext_function_property_write_r.dmp_ext_function_property_write_r_conn`'s
    own ``return_code`` (Function Property specific, left to the caller),
    ``PID_RUN_STATE_CONTROL`` is a ``PDT_CONTROL`` property, for which the
    Application Layer defines a fixed response shape (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.8.4): a positive ``return_code``
    always carries the 1 octet state, a negative one always carries none.
    So a negative ``return_code`` here is unambiguously an error, not a
    function-specific result to interpret - and is raised rather than
    returned.

    ``max_apdu_length`` is required: the fixed 10 octet run event plus the
    6 octet ``A_FunctionPropertyExtCommand`` header
    (``const.FUNCTION_PROPERTY_EXT_HEADER_OCTETS``) is 16 octets, one past
    the 15 octet standard-frame fallback, and the spec allows no shorter
    command ("The format of command shall be identical to the one specified
    for DMP_RunStateMachineWrite_R_IO in 3.34.3"; KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.8.4: "exactly the 10 octet data"). A
    device answering only standard frames can never accept this procedure;
    pass the device's real ``PID_MAX_APDU_LENGTH`` (KNX v01.10.01 -
    Resources 03.05.01 - §4.3.7).

    Unlike the non-extended procedure, this one doesn't poll for an expected
    state (the "verify the resulting state" flag of DM_RunStateMachineWrite,
    §3.34.1); follow it with
    :func:`~.dmp_ext_run_state_machine_verify_r_co_io.dmp_ext_run_state_machine_verify_r_co_io`
    or poll with
    :func:`~.dmp_ext_run_state_machine_read_r_co_io.dmp_ext_run_state_machine_read_r_co_io`
    instead.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :param event_data: The 10 octet run event
    :param max_apdu_length: The device's PID_MAX_APDU_LENGTH; must be at
        least 16 (6 octet header + the fixed 10 octet event)
    :return: The resulting Run State
    :raises ValueError: If ``event_data`` is not exactly 10 octets, or it
        does not fit within ``max_apdu_length``
    :raises ManagementConnectionError: If the device returns a negative
        return code, or the resulting Run State is not a valid state
    """
    check_event_size(event_data)
    context = ext_context(interface_object_type, object_instance)
    response = await dmp_ext_function_property_write_r_conn(
        conn,
        interface_object_type=interface_object_type,
        object_instance=object_instance,
        property_id=ResourceGenericPropertyId.PID_RUN_STATE_CONTROL,
        command=event_data,
        max_apdu_length=max_apdu_length,
    )
    return decode_run_state(
        pdt_control_state_data(response, f"{context} Run State Machine write"),
        context,
    )
