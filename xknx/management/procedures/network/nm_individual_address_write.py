"""NM_IndividualAddress_Write — KNX 03.05.02 §2.3."""

from __future__ import annotations

import logging

from xknx.exceptions import ManagementConnectionError, ManagementConnectionRefused
from xknx.management.procedures.device.dm_restart_r_co import dm_restart
from xknx.management.procedures.network.nm_individual_address_check import (
    nm_individual_address_check,
)
from xknx.management.procedures.network.nm_individual_address_read import (
    nm_individual_address_read,
)
from xknx.management.protocols import Broadcaster, ConnectionManager
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_write(
    manager: ConnectionManager,
    broadcaster: Broadcaster,
    individual_address: IndividualAddressableType,
) -> None:
    """
    Write the individual address of a single device in programming mode.

    :param manager: connection manager used to open P2P connections
    :param broadcaster: broadcaster for sending and receiving broadcast telegrams
    :param individual_address: address to be written to KNX device
    """
    logger.debug("Writing individual address %s to device.", individual_address)

    # check if the address is already occupied on the network
    individual_address = IndividualAddress(individual_address)
    try:
        async with manager.connection(individual_address) as conn:
            address_found = await nm_individual_address_check(conn)
    except ManagementConnectionRefused:
        # KNX 03.05.02 §2.3 step 1: "if A_Disconnect-PDU is received then IA_new shall be
        # regarded as occupied". nm_individual_address_check already handled this and returned
        # True; this except swallows ManagementConnectionRefused from disconnect() in finally.
        pass

    if address_found:
        logger.debug(
            "Individual address %s already present on the bus", individual_address
        )

    # check which devices are in programming mode
    dev_pgm_mode = await nm_individual_address_read(
        broadcaster, raise_if_multiple=True
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
        await broadcaster.send_broadcast(
            payload=apci.IndividualAddressWrite(address=individual_address),
        )
        logger.debug("Wrote new address %s to device.", individual_address)

    async with manager.connection(address=individual_address) as connection:
        logger.debug(
            "Checking if device exists at %s and restarting it.", individual_address
        )
        if not await nm_individual_address_check(connection):
            raise ManagementConnectionError(
                "No device answered to connection attempt after write address operation."
            )
        logger.debug("Restarting device, exiting programming mode.")
        await dm_restart(connection)
