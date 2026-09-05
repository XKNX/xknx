"""DMP_ExtFunctionProperty_Write_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.management.management import P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .const import FUNCTION_PROPERTY_EXT_HEADER_OCTETS

if TYPE_CHECKING:
    from xknx import XKNX

__all__ = [
    "dmp_ext_function_property_write_r",
    "dmp_ext_function_property_write_r_conn",
]


async def dmp_ext_function_property_write_r_conn(
    conn: P2PConnection,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    command: bytes,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> apci.FunctionPropertyExtStateResponse:
    """
    Invoke an extended Function Property over an open connection.

    DMP_ExtFunctionProperty_Write_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.2. Addresses the interface object by Interface Object
    Type + Object Instance rather than the connection-local object index
    :func:`~.dm_function_property_write_r.dm_function_property_write_r_conn`
    uses. If used in point-to-point connection-oriented mode (as this
    ``_conn`` variant does), a DMP_Connect_RCo must be performed first.

    As with the base (non-extended) procedure, ``return_code``'s meaning and
    error handling are Function Property specific and depend on the
    Configuration Procedure using this one, so the full response is returned
    rather than raised on anything other than success. Likewise, ``command``
    is not chunked when it doesn't fit ``max_apdu_length`` - it is rejected
    upfront instead.

    :param conn: Active P2P connection to the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :param property_id: 12 bit Property Identifier
    :param command: Function Property specific command data
    :param max_apdu_length: Caps ``command`` so its
        A_FunctionPropertyExtCommand-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's fallback of 15 octets for a device
        whose actual value hasn't been read; pass the real value for a
        device known to support more.
    :return: The device's A_FunctionPropertyExtState_Response (return code
        and resulting state data)
    :raises ValueError: If ``command`` does not fit within ``max_apdu_length``
    """
    max_command_length = max_apdu_length - FUNCTION_PROPERTY_EXT_HEADER_OCTETS
    if len(command) > max_command_length:
        raise ValueError(
            f"command ({len(command)} octets) does not fit max_apdu_length "
            f"{max_apdu_length} (header is "
            f"{FUNCTION_PROPERTY_EXT_HEADER_OCTETS} octets, leaving "
            f"{max_command_length} for command data)"
        )
    response = await conn.request(
        apci.FunctionPropertyExtCommand(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            data=command,
        )
    )
    return response.payload


async def dmp_ext_function_property_write_r(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    command: bytes,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> apci.FunctionPropertyExtStateResponse:
    """
    Invoke an extended Function Property, opening and closing a connection.

    DMP_ExtFunctionProperty_Write_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.2. See
    :func:`dmp_ext_function_property_write_r_conn` for details.

    :param xknx: the XKNX object
    :param individual_address: address of the device
    :param interface_object_type: 16 bit Interface Object Type
    :param object_instance: 12 bit Object Instance
    :param property_id: 12 bit Property Identifier
    :param command: Function Property specific command data
    :param max_apdu_length: Caps ``command`` so its
        A_FunctionPropertyExtCommand-PDU fits within this many octets - see
        :func:`dmp_ext_function_property_write_r_conn`.
    :return: The device's A_FunctionPropertyExtState_Response (return code
        and resulting state data)
    :raises ValueError: If ``command`` does not fit within ``max_apdu_length``
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        return await dmp_ext_function_property_write_r_conn(
            conn,
            interface_object_type,
            object_instance,
            property_id,
            command,
            max_apdu_length,
        )
