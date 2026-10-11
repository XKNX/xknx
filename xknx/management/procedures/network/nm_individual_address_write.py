"""NM_IndividualAddress_Write — KNX v02.01.02 - Management Procedures 03.05.02 - §2.3."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dm_restart_r_co import dm_restart_r_co
from xknx.management.procedures.network.nm_individual_address_check import (
    nm_individual_address_check,
    nm_individual_address_check_conn,
)
from xknx.management.procedures.network.nm_individual_address_read import (
    nm_individual_address_read,
)
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")

# Time-out of each A_IndividualAddress_Read while waiting for a device in programming
# mode - KNX v02.01.02 - Management Procedures 03.05.02 - §2.3 step 2.
PROGRAMMING_MODE_POLL_TIMEOUT = 1.0


async def nm_individual_address_write(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    wait_for_programming_mode: float | None = None,
) -> None:
    """
    Write the individual address of a single device in programming mode.

    :param xknx: the XKNX object
    :param individual_address: address to be written to KNX device
    :param wait_for_programming_mode: Seconds to wait for a device in programming
        mode, eg. while the user presses its programming button. A_IndividualAddress_Read
        is repeated with a time-out of PROGRAMMING_MODE_POLL_TIMEOUT until a device
        answers, as KNX v02.01.02 - Management Procedures 03.05.02 - §2.3 step 2
        describes. ``None`` (the default) reads once.
    :raises ManagementConnectionError: If no device or more than one device is in
        programming mode, another device already uses ``individual_address``, or the
        device doesn't answer at the new address
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
    # raises exception if more than one device in programming mode
    dev_pgm_mode = await _devices_in_programming_mode(xknx, wait_for_programming_mode)
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
        await xknx.management.broadcast.send(
            payload=apci.IndividualAddressWrite(address=individual_address),
        )
        logger.debug("Wrote new address %s to device.", individual_address)

    async with xknx.management.connection(address=individual_address) as connection:
        logger.debug(
            "Checking if device exists at %s and restarting it.", individual_address
        )
        if not await nm_individual_address_check_conn(connection):
            raise ManagementConnectionError(
                "No device answered to connection attempt after write address operation."
            )
        logger.debug("Restarting device, exiting programming mode.")
        await dm_restart_r_co(connection)


async def _devices_in_programming_mode(
    xknx: XKNX, wait: float | None
) -> list[IndividualAddress]:
    """Read the devices in programming mode, polling for up to ``wait`` seconds."""
    if wait is None:
        return await nm_individual_address_read(xknx, raise_if_multiple=True)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + wait
    while True:
        devices = await nm_individual_address_read(
            xknx, timeout=PROGRAMMING_MODE_POLL_TIMEOUT, raise_if_multiple=True
        )
        if devices or loop.time() >= deadline:
            return devices
        logger.debug("Waiting for a device in programming mode.")
