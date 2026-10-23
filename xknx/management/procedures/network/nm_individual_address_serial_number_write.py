"""NM_IndividualAddress_SerialNumber_Write — KNX v02.01.02 - Management Procedures 03.05.02 - §2.5."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.network.nm_individual_address_check import (
    nm_individual_address_check,
)
from xknx.management.procedures.network.nm_individual_address_serial_number_read import (
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
    """
    Write individual address to device with specified serial number.

    KNX v02.01.02 - Management Procedures 03.05.02 - §2.5 requires the procedure
    to ensure that the assigned Individual Address is unique, but names no
    mechanism for it. ``individual_address`` is checked the same way
    NM_IndividualAddress_Write (KNX v02.01.02 - Management Procedures 03.05.02 -
    §2.3 step 1) does. If a device answers there, the device with ``serial`` is
    asked for its current address: if it already has ``individual_address``,
    nothing is written (like §2.3 step 3); otherwise nothing is written and
    ManagementConnectionError is raised.

    When no device answers at ``individual_address``, the check takes about 6 s
    (A_DeviceDescriptor_Read and its retransmit, 3 s each) before the address is written.

    :param xknx: the XKNX object
    :param serial: KNX Serial Number of the device
    :param individual_address: address to be written to the device
    :raises ManagementConnectionError: If another device already uses
        ``individual_address``, the address is in use and no device with
        ``serial`` answers, or the device doesn't confirm the new address
    """
    individual_address = IndividualAddress(individual_address)
    logger.debug(
        "Writing individual address %s to device with serial number %s.",
        individual_address,
        serial,
    )
    if await nm_individual_address_check(xknx, individual_address):
        logger.debug(
            "Individual address %s already present on the bus", individual_address
        )
        current = await nm_individual_address_serial_number_read(
            xknx=xknx, serial=serial
        )
        if current is None:
            logger.debug("No device with serial number %s answered.", serial)
            raise ManagementConnectionError(
                f"Individual address {individual_address} is already in use and no "
                f"device with serial {serial!r} answered, cannot write the address."
            )
        if current != individual_address:
            logger.debug(
                "Device with address %s found and it is not the one with serial number %s. Exiting to prevent address conflict.",
                individual_address,
                serial,
            )
            raise ManagementConnectionError(
                f"Individual address {individual_address} is already in use by another "
                f"device, cannot write it to device with serial {serial!r}."
            )
        # the serial number read above already verified the address
        logger.debug(
            "Device with serial number %s already has requested address %s, no write operation needed.",
            serial,
            individual_address,
        )
        return
    await xknx.management.broadcast.send(
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
