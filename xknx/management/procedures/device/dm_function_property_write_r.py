"""DM_FunctionProperty_Write_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.1."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.management.management import P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

__all__ = ["dm_function_property_write_r", "dm_function_property_write_r_conn"]


async def dm_function_property_write_r_conn(
    conn: P2PConnection,
    object_index: int,
    property_id: int,
    command: bytes,
) -> apci.FunctionPropertyStateResponse:
    """
    Invoke a Function Property on an interface object over an open connection.

    DM_FunctionProperty_Write_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.1. If used in point-to-point connection-oriented mode
    (as this ``_conn`` variant does), a DMP_Connect_RCo must be performed
    first.

    The command coding and the meaning of ``return_code`` are Function
    Property specific (KNX v02.01.01 - Application Interface Layer 03.04.01),
    and per the spec's own "Error handling" clause their interpretation
    "depends on the Configuration Procedure in which this Management
    Procedure is used" - so this does not raise on a non-zero return code,
    it is returned to the caller to interpret.

    There is no separate DM_/DMP_ Management Procedure to read a (non
    extended) Function Property's state without invoking a command - send
    ``apci.FunctionPropertyStateRead`` via ``conn.request()`` directly for
    that.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param command: Function Property specific command data
    :return: The device's A_FunctionPropertyState_Response (return code and
        resulting state data)
    """
    response = await conn.request(
        apci.FunctionPropertyCommand(
            object_index=object_index, property_id=property_id, data=command
        )
    )
    return response.payload


async def dm_function_property_write_r(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    object_index: int,
    property_id: int,
    command: bytes,
) -> apci.FunctionPropertyStateResponse:
    """
    Invoke a Function Property on a device, opening and closing a connection.

    DM_FunctionProperty_Write_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.30.1. See :func:`dm_function_property_write_r_conn` for
    details.

    :param xknx: the XKNX object
    :param individual_address: address of the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param command: Function Property specific command data
    :return: The device's A_FunctionPropertyState_Response (return code and
        resulting state data)
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        return await dm_function_property_write_r_conn(
            conn, object_index, property_id, command
        )
