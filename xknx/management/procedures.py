"""Package for management procedures as described in KNX-Standard 3.5.2."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import (
    ManagementConnectionError,
    ManagementConnectionRefused,
    ManagementConnectionTimeout,
)
from xknx.telegram import Telegram, apci, tpci
from xknx.telegram.address import (
    GroupAddress,
    IndividualAddress,
    IndividualAddressableType,
)

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


class AsyncAddressResponseHandler:
    """Class to handle responses to IndividualAddressRead broadcast telegrams."""

    def __init__(self) -> None:
        """Initialise AsyncAddressResponseHandler."""
        self.queue: list[Telegram] = []

    def process(self, telegram: Telegram) -> None:
        """Handle incoming telegram."""
        if isinstance(telegram.payload, apci.IndividualAddressResponse):
            self.queue.append(telegram)

    def clear(self) -> None:
        """Empty telegram buffer."""
        self.queue.clear()


async def dm_restart(xknx: XKNX, individual_address: IndividualAddressableType) -> None:
    """Restart the device."""
    async with xknx.management.connection(
        address=IndividualAddress(individual_address)
    ) as connection:
        logger.debug("Requesting a Basic Restart of %s.", individual_address)
        # A_Restart will not be ACKed by the device, so it is manually sent to avoid timeout and retry
        seq_num = next(connection.sequence_number)
        telegram = Telegram(
            destination_address=connection.address,
            source_address=xknx.current_address,
            payload=apci.Restart(),
            tpci=tpci.TDataConnected(sequence_number=seq_num),
        )
        await xknx.cemi_handler.send_telegram(telegram)


async def nm_individual_address_check(
    xknx: XKNX, individual_address: IndividualAddressableType
) -> bool:
    """Check if the individual address is occupied on the network."""
    try:
        async with xknx.management.connection(
            address=IndividualAddress(individual_address)
        ) as connection:
            try:
                response = await connection.request(
                    payload=apci.DeviceDescriptorRead(descriptor=0),
                    expected=apci.DeviceDescriptorResponse,
                )

            except ManagementConnectionTimeout as ex:
                # if nothing is received (-> timeout) IA is free
                logger.debug("No device answered to connection attempt. %s", ex)
                return False
            if isinstance(response.payload, apci.DeviceDescriptorResponse):
                # if response is received IA is occupied
                logger.debug("Device found at %s", individual_address)
                return True
            return False
    except ManagementConnectionRefused as ex:
        # if Disconnect is received immediately, IA is occupied
        logger.debug("Device does not support transport layer connections. %s", ex)
        return True


async def nm_individual_address_read(
    xknx: XKNX, timeout: int = 3
) -> list[IndividualAddress]:
    """
    Request individual addresses of all devices that are in programming mode.

    :param: timeout specifies the timeout in seconds, the KNX specification requires a timeout of 3s.
    """

    addresses = []
    # initialize queue or event handler gathering broadcasts
    async with xknx.management.broadcast() as bc_context:
        broadcast_telegram = Telegram(
            GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
        )
        await xknx.management.send_broadcast(broadcast_telegram)
        async for result in bc_context.receive(timeout=3):
            if isinstance(result.payload, apci.IndividualAddressResponse):
                addresses.append(result.source_address)
    return addresses


async def nm_invididual_address_write(
    xknx: XKNX, individual_address: IndividualAddressableType
) -> None:
    """
    Write the individual address of a single device in programming mode.

    TODO: detail exceptions if this failed.
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
    dev_pgm_mode = await nm_individual_address_read(xknx)
    if len(dev_pgm_mode) > 1:
        logger.debug("More than one device in programming mode detected.")
        raise ManagementConnectionError("More than one device is programming mode.")
    if len(dev_pgm_mode) == 0:
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
            Telegram(
                GroupAddress("0/0/0"),
                payload=apci.IndividualAddressWrite(address=individual_address),
            )
        )
        logger.debug("Wrote new address %s to device.", individual_address)

    async with xknx.management.connection(
        address=IndividualAddress(individual_address)
    ) as connection:
        logger.debug(
            "Checking if device exists at %s and restarting it.", individual_address
        )

        try:
            response = await connection.request(
                payload=apci.DeviceDescriptorRead(descriptor=0),
                expected=apci.DeviceDescriptorResponse,
            )
        except ManagementConnectionTimeout as ex:
            # if nothing is received (-> timeout) IA is free
            logger.debug("No device answered to connection attempt. %s", ex)
            response = None
        if response and isinstance(response.payload, apci.DeviceDescriptorResponse):
            # if response is received IA is occupied
            logger.debug("Device found at %s", individual_address)
        else:
            raise ManagementConnectionError(
                f"Failed to detect individual address ({individual_address}) after write address operation."
            )

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
