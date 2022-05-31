"""Package for management procedures as described in KNX-Standard 3.5.2."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionRefused, ManagementConnectionTimeout
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_check(
    xknx: XKNX, individual_address: IndividualAddressableType
) -> bool:
    """Check if the individual address is occupied on the network."""
    _ia = IndividualAddress(individual_address)
    async with xknx.management.connection(address=_ia) as connection:
        try:
            response = await connection.request(
                payload=apci.DeviceDescriptorRead(descriptor=0),
                expected=apci.DeviceDescriptorResponse,
            )
        except ManagementConnectionRefused as ex:
            # if Disconnect is received immediately, IA is occupied
            logger.debug("Device does not support transport layer connections. %s", ex)
            return True
        except ManagementConnectionTimeout as ex:
            # if nothing is received (-> timeout) IA is free
            logger.debug("No device answered to connection attempt. %s", ex)
            return False
        if isinstance(response.payload, apci.DeviceDescriptorResponse):
            # if response is received IA is occupied
            logger.debug("Device found at %s", individual_address)
            return True
        return False
