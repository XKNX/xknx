"""NM_IndividualAddress_Check — KNX 03.05.02 §2.19."""

from __future__ import annotations

import logging

from xknx.exceptions import ManagementConnectionRefused, ManagementConnectionTimeout
from xknx.management.protocols import P2PConnection
from xknx.telegram import apci

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_check(conn: P2PConnection) -> bool:
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
