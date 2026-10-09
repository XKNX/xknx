"""DM_FunctionProperty_Write_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.1."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import ConnectionlessP2P, P2PConnection
from xknx.telegram import apci

__all__ = ["dm_function_property_write_r"]


async def dm_function_property_write_r(
    conn: P2PConnection | ConnectionlessP2P,
    object_index: int,
    property_id: int,
    command: bytes = b"",
) -> apci.FunctionPropertyStateResponse:
    """
    Call a Function Property of an Interface Object.

    DM_FunctionProperty_Write_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.1: "This Management Procedure shall use point-to-point
    connection-oriented or point-to-point connectionless communication mode.
    In case the point-to-point connection-oriented communication mode is
    used, a DMP_Connect_RCo shall be performed preceding this procedure." So
    `conn` is either an open `P2PConnection` or a `ConnectionlessP2P`.

    Sends an A_FunctionPropertyCommand-PDU with `command` as data, answered by
    an A_FunctionPropertyState_Response-PDU carrying the return_code and the
    function's output data.

    :param conn: Active P2P connection or connectionless communication with
        the device
    :param object_index: Index of the Interface Object (0-255)
    :param property_id: Property identifier of the Function Property (0-255)
    :param command: Function Property specific input data
    :return: The device's response. Its `return_code` is the procedure's
        "error" - Function Property specific, so it is not judged here (§3.30.1
        Error handling: "The handling of this error depends on the
        Configuration Procedure in which this Management Procedure is used.").
        It is None if the Property is not a Function Property (KNX v02.01.01 -
        Application Layer 03.03.07 - §3.4.7.3).
    :raises ValueError: If object_index or property_id is out of range
    :raises ManagementConnectionError: If the response is for another
        Interface Object or Property
    """
    if not 0 <= object_index <= 0xFF:
        raise ValueError(f"object_index must be 0-255, got {object_index}")
    if not 0 <= property_id <= 0xFF:
        raise ValueError(f"property_id must be 0-255, got {property_id}")
    response = await conn.request(
        apci.FunctionPropertyCommand(
            object_index=object_index, property_id=property_id, data=command
        )
    )
    payload = response.payload
    # Not in spec: the response repeats object_index and Property_id
    # (§3.30.1 Sequence), so one for another Function Property is not ours.
    if payload.object_index != object_index or payload.property_id != property_id:
        raise ManagementConnectionError(
            f"Function Property response for object {payload.object_index} "
            f"PID {payload.property_id}, expected object {object_index} "
            f"PID {property_id}"
        )
    return payload
