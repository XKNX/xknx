"""DMP_ExtLoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.5."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId

from ._pdt_control import pdt_control_state_data
from .dmp_ext_function_property_write_r import dmp_ext_function_property_write_r_conn
from .load_state import LOAD_EVENT_SIZE, LoadState, decode_load_state

__all__ = ["dmp_ext_load_state_machine_write_r_co_io"]


async def dmp_ext_load_state_machine_write_r_co_io(
    conn: P2PConnection,
    interface_object_type: int,
    object_instance: int,
    event_data: bytes,
    *,
    max_apdu_length: int,
) -> LoadState:
    """
    Write a load event to an extended-addressed Load State Machine.

    DMP_ExtLoadStateMachineWrite_RCo_IO — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.31.5. Addresses the interface object by
    Interface Object Type + Object Instance rather than the connection-local
    object index
    :func:`~.dmp_load_state_machine_write_r_co_io.dmp_load_state_machine_write_r_co_io`
    uses. "The format of command shall be identical to the one specified for
    DMP_LoadStateMachineWrite_RCo_IO in 3.31.3" - see
    :mod:`xknx.management.procedures.device.load_state` for the builders.
    Uses the connection-oriented mode, as the spec requires.

    Sent as ``A_FunctionPropertyExtCommand``. ``PID_LOAD_STATE_CONTROL`` is
    ``PDT_CONTROL``, so the response shape is fixed (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.8.4): a positive ``return_code``
    carries the 1 octet state, a negative one is an error and is raised.

    Unlike the non-extended procedure, this one doesn't poll for an
    expected state; use DMP_ExtLoadStateMachineVerify/Read for that.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :param event_data: The 10 octet load event
    :param max_apdu_length: The device's PID_MAX_APDU_LENGTH (KNX v01.10.01 -
        Resources 03.05.01 - §4.3.7). Required: the fixed 10 octet event
        plus the 6 octet ``A_FunctionPropertyExtCommand`` header is 16
        octets, so the 15 octet standard-frame fallback can never fit and
        the device must support L_Data_Extended frames.
    :return: The resulting Load State
    :raises ValueError: If ``event_data`` is not exactly 10 octets, or it
        does not fit within ``max_apdu_length``
    :raises ManagementConnectionError: If the device returns a negative
        return code, the response doesn't echo the request, or the resulting
        Load State is not a valid state
    """
    if len(event_data) != LOAD_EVENT_SIZE:
        raise ValueError(
            f"event_data must be {LOAD_EVENT_SIZE} octets, got {len(event_data)}"
        )
    context = (
        f"interface object type {interface_object_type} instance {object_instance}"
    )
    response = await dmp_ext_function_property_write_r_conn(
        conn,
        interface_object_type=interface_object_type,
        object_instance=object_instance,
        property_id=ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
        command=event_data,
        max_apdu_length=max_apdu_length,
    )
    return decode_load_state(
        pdt_control_state_data(response, f"{context} Load State Machine write"),
        context,
    )
