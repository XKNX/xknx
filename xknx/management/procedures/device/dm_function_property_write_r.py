"""DM_FunctionProperty_Write_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci


async def dm_function_property_write_r(
    conn: P2PConnection, object_index: int, property_id: int, command: bytes
) -> apci.FunctionPropertyStateResponse:
    """
    Execute a Function Property of a device and return its answer.

    Sends A_FunctionPropertyCommand over an open connection (DMP_Connect_RCo
    first). The A_FunctionPropertyState_Response carries the return code and the
    data; their meaning is specific to the Function Property, so it is returned as
    it is.

    :param conn: an open connection to the device
    :param object_index: the Interface Object of the Function Property
    :param property_id: the Function Property
    :param command: the command, specific to the Function Property
    :raises ManagementConnectionError: when the answer is not for this Function Property
    """
    telegram = await conn.request(
        apci.FunctionPropertyCommand(
            object_index=object_index, property_id=property_id, data=command
        )
    )
    response = telegram.payload
    if (
        not isinstance(response, apci.FunctionPropertyStateResponse)
        or response.object_index != object_index
        or response.property_id != property_id
    ):
        raise ManagementConnectionError(
            f"No Function Property response for object {object_index} "
            f"property {property_id}: {response}"
        )
    return response
