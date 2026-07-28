"""NM_IndividualAddress_Check — KNX 03.05.02 §2.19."""

from __future__ import annotations

import logging

from xknx.exceptions import ManagementConnectionRefused, ManagementConnectionTimeout
from xknx.management.management import Management, P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_check_conn(conn: P2PConnection) -> bool:
    """
    Check if a device responds on an already-open connection.

    Returns True if the device answers, False on timeout.
    ManagementConnectionRefused propagates to the caller.

    :param conn: an established P2P connection to the device
    """
    try:
        response = await conn.request(
            payload=apci.DeviceDescriptorRead(descriptor=0),
            expected=apci.DeviceDescriptorResponse,
        )
        if isinstance(response.payload, apci.DeviceDescriptorResponse):
            logger.debug("Device found at %s", conn.address)
            return True
        return False
    except ManagementConnectionTimeout as ex:
        logger.debug("No device answered to connection attempt. %s", ex)
        return False
    except ManagementConnectionRefused as ex:
        # if Disconnect is received immediately, IA is occupied
        logger.debug("Device does not support transport layer connections. %s", ex)
        return True


async def nm_individual_address_check(
    management: Management, individual_address: IndividualAddressableType
) -> bool:
    """
    Check if a device responds, opening and closing a connection to it.

    Returns True if the device answers or refuses the connection (per KNX
    03.05.02 §2.3 step 1, an A_Disconnect-PDU means the address is occupied),
    False on timeout.

    :param management: connection manager used to open a P2P connection
    :param individual_address: address to check
    """
    address_found = False
    try:
        async with management.connection(IndividualAddress(individual_address)) as conn:
            address_found = await nm_individual_address_check_conn(conn)
    except ManagementConnectionRefused:
        address_found = True
    return address_found
