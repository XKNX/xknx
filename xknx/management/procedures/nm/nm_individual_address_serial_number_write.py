"""NM_IndividualAddress_SerialNumber_Write — KNX 03.05.02 §2.5."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.nm.nm_individual_address_serial_number_read import (
    nm_individual_address_serial_number_read,
)
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_serial_number_write(
    xknx: XKNX, serial: bytes, individual_address: IndividualAddressableType
) -> None:
    """Write individual address to device with specified serial number."""
    individual_address = IndividualAddress(individual_address)
    await xknx.management.send_broadcast(
        payload=apci.IndividualAddressSerialWrite(
            address=individual_address,
            serial=serial,
        )
    )
    logger.debug(
        "Wrote new address %s to device with serial number %s.",
        individual_address,
        serial,
    )

    address = await nm_individual_address_serial_number_read(xknx=xknx, serial=serial)

    if address is None:
        raise ManagementConnectionError(f"No reply received from {serial!r}.")

    if address != individual_address:
        raise ManagementConnectionError(
            f"Failed to write serial address {individual_address} to device with serial {serial!r}. Detected {address}"
        )

    logger.debug(
        "New address %s validated on device with serial number %s.",
        individual_address,
        serial,
    )
