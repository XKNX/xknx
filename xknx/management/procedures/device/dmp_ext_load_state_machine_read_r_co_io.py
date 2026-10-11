"""DMP_ExtLoadStateMachineRead_RCo_IO — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.4."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import LoadState, ResourceGenericPropertyId
from xknx.telegram import Telegram, apci

from ._load_state_machine import decode_load_state

__all__ = ["dmp_ext_load_state_machine_read_r_co_io"]


def ext_state_response_load_state(telegram: Telegram) -> LoadState:
    """Return the Load State of an A_FunctionPropertyExtState_Response."""
    payload = telegram.payload
    if not isinstance(payload, apci.FunctionPropertyExtStateResponse):
        raise ManagementConnectionError(
            f"Load State Machine: unexpected response {payload}"
        )
    if payload.return_code is not apci.ReturnCode.E_SUCCESS:
        raise ManagementConnectionError(
            f"Load State Machine: device returned {payload.return_code.name}"
        )
    return decode_load_state(payload.data)


async def dmp_ext_load_state_machine_read_r_co_io(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    property_id: int = ResourceGenericPropertyId.PID_LOAD_STATE_CONTROL,
) -> LoadState:
    """
    Read the state of a Load State Machine with A_FunctionPropertyExtState_Read.

    DMP_ExtLoadStateMachineRead_RCo_IO — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.33.4. Addresses the Interface Object by type and instance
    instead of by index. Requires an established connection (DM_Connect must
    be executed first).

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type hosting the Load State Machine -
        see ResourceObjectType
    :param object_instance: Instance of that Interface Object Type
    :param property_id: Property of the Load State Machine
    :return: The current Load State
    :raises ManagementConnectionError: If the device answers with a negative
        return code, no data or an unknown state
    """
    response = await conn.request(
        payload=apci.FunctionPropertyExtStateRead(
            interface_object_type=object_type,
            object_instance=object_instance,
            property_id=property_id,
        ),
    )
    return ext_state_response_load_state(response)
