"""NM_IndividualAddress_SerialNumber_Write — KNX 03.05.02 §2.5."""

from __future__ import annotations

import logging

from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.network.nm_individual_address_serial_number_read import (
    nm_individual_address_serial_number_read,
)
from xknx.management.protocols import Broadcaster
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_serial_number_write(
    broadcaster: Broadcaster,
    serial: bytes,
    individual_address: IndividualAddressableType,
) -> None:
    """Write individual address to device with specified serial number."""
    individual_address = IndividualAddress(individual_address)
    await broadcaster.send_broadcast(
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

    address = await nm_individual_address_serial_number_read(broadcaster, serial=serial)

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
