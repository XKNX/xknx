"""DMP_ExtFunctionProperty_Write_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.2."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import ConnectionlessP2P, P2PConnection
from xknx.telegram import apci

__all__ = [
    "dmp_ext_function_property_write_r",
    "dmp_ext_function_property_write_r_cl",
]


async def dmp_ext_function_property_write_r(
    conn: P2PConnection,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    command: bytes = b"",
) -> apci.FunctionPropertyExtStateResponse:
    """
    Call a Function Property of an Interface Object, addressed by its type and instance.

    DMP_ExtFunctionProperty_Write_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.2: "This Management Procedure shall use the connection
    oriented or connectionless communication mode." So `conn` is an open
    `P2PConnection`; `dmp_ext_function_property_write_r_cl` is the same
    procedure in the connectionless communication mode.

    Sends an A_FunctionPropertyExtCommand-PDU with `command` as data, answered
    by an A_FunctionPropertyExtState_Response-PDU carrying the return_code and
    the function's output data.

    :param conn: Active P2P connection with the device
    :param interface_object_type: Interface Object Type (0-65535)
    :param object_instance: Object Instance (0-4095)
    :param property_id: Property identifier of the Function Property (0-4095)
    :param command: Function Property specific input data
    :return: The device's response. Its `return_code` is not judged here
        (§3.30.2 Exception handling: "The error shall be Function Property
        specific [...]. The handling of this error depends on the Configuration
        Procedure in which this Management Procedure is used.").
    :raises ValueError: If interface_object_type, object_instance or
        property_id is out of range
    :raises ManagementConnectionError: If the response is for another
        Interface Object or Property
    """
    return await _ext_function_property_write(
        conn, interface_object_type, object_instance, property_id, command
    )


async def dmp_ext_function_property_write_r_cl(
    connectionless: ConnectionlessP2P,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    command: bytes = b"",
) -> apci.FunctionPropertyExtStateResponse:
    """
    Call a Function Property connectionless, addressed by object type and instance.

    DMP_ExtFunctionProperty_Write_R in the point-to-point connectionless
    communication mode - suffix RCl, KNX v02.01.02 - Management Procedures
    03.05.02 - §1.2 Table 1 - which §3.30.2 allows as well. Arguments, result
    and errors are those of `dmp_ext_function_property_write_r`.

    :param connectionless: Connectionless communication with the device, from
        `xknx.management.connectionless()`
    """
    return await _ext_function_property_write(
        connectionless, interface_object_type, object_instance, property_id, command
    )


async def _ext_function_property_write(
    conn: P2PConnection | ConnectionlessP2P,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    command: bytes,
) -> apci.FunctionPropertyExtStateResponse:
    """Run DMP_ExtFunctionProperty_Write_R in either communication mode."""
    if not 0 <= interface_object_type <= 0xFFFF:
        raise ValueError(
            f"interface_object_type must be 0-65535, got {interface_object_type}"
        )
    if not 0 <= object_instance <= 0xFFF:
        raise ValueError(f"object_instance must be 0-4095, got {object_instance}")
    if not 0 <= property_id <= 0xFFF:
        raise ValueError(f"property_id must be 0-4095, got {property_id}")
    response = await conn.request(
        apci.FunctionPropertyExtCommand(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            data=command,
        )
    )
    payload = response.payload
    # Not in spec: the response repeats object_type, object_instance and PID
    # (§3.30.2 Sequence), so one for another Function Property is not ours.
    if (
        payload.interface_object_type != interface_object_type
        or payload.object_instance != object_instance
        or payload.property_id != property_id
    ):
        raise ManagementConnectionError(
            "Function Property response for object type "
            f"{payload.interface_object_type} instance {payload.object_instance} "
            f"PID {payload.property_id}, expected object type "
            f"{interface_object_type} instance {object_instance} PID {property_id}"
        )
    return payload
