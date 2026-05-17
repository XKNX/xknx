"""NM_IndividualAddress_Write — KNX 03.05.02 §2.3."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError, ManagementConnectionTimeout
from xknx.management.procedures.network.nm_individual_address_check import (
    nm_individual_address_check,
)
from xknx.management.procedures.network.nm_individual_address_read import (
    nm_individual_address_read,
)
from xknx.telegram import Telegram, apci, tpci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_write(
    xknx: XKNX, individual_address: IndividualAddressableType
) -> None:
    """
    Write the individual address of a single device in programming mode.

    :param xknx: XKNX object
    :param individual_address: address to be written to KNX device
    """
    logger.debug("Writing individual address %s to device.", individual_address)

    # check if the address is already occupied on the network
    individual_address = IndividualAddress(individual_address)
    address_found = await nm_individual_address_check(xknx, individual_address)

    if address_found:
        logger.debug(
            "Individual address %s already present on the bus", individual_address
        )

    # check which devices are in programming mode
    dev_pgm_mode = await nm_individual_address_read(
        xknx, raise_if_multiple=True
    )  # raises exception if more than one device in programming mode
    if not dev_pgm_mode:
        logger.debug("No device in programming mode detected.")
        raise ManagementConnectionError("No device in programming mode detected.")

    # check if new and received addresses match
    if address_found:
        if individual_address != dev_pgm_mode[0]:
            logger.debug(
                "Device with address %s found and it is not in programming mode. Exiting to prevent address conflict.",
                individual_address,
            )
            raise ManagementConnectionError(
                f"A device was found with {individual_address}, cannot continue with programming."
            )
        # device in programming mode's address matches address that we want to write, so we can abort the operation safely
        logger.debug("Device already has requested address, no write operation needed.")
    else:
        await xknx.management.send_broadcast(
            payload=apci.IndividualAddressWrite(address=individual_address),
        )
        logger.debug("Wrote new address %s to device.", individual_address)

    async with xknx.management.connection(
        address=IndividualAddress(individual_address)
    ) as connection:
        logger.debug(
            "Checking if device exists at %s and restarting it.", individual_address
        )

        try:
            await connection.request(
                payload=apci.DeviceDescriptorRead(descriptor=0),
                expected=apci.DeviceDescriptorResponse,
            )
        except ManagementConnectionTimeout as ex:
            # if nothing is received (-> timeout) IA is free
            raise ManagementConnectionError(
                f"No device answered to connection attempt after write address operation. {ex}"
            ) from None

        logger.debug("Restating device, exiting programming mode.")
        # A_Restart will not be ACKed by the device, so it is manually sent to avoid timeout and retry
        seq_num = next(connection.sequence_number)
        telegram = Telegram(
            destination_address=connection.address,
            source_address=xknx.current_address,
            payload=apci.Restart(),
            tpci=tpci.TDataConnected(sequence_number=seq_num),
        )
        await xknx.cemi_handler.send_telegram(telegram)
