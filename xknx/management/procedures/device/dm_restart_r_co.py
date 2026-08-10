"""DM_Restart_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.management.management import P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def dm_restart_r_co(conn: P2PConnection) -> None:
    """
    Restart the device on an already-open connection.

    :param conn: an established P2P connection to the device
    """
    logger.debug("Requesting a Basic Restart of %s.", conn.address)
    await conn.send_data(apci.Restart(), wait_for_ack=False)


async def dm_restart(xknx: XKNX, individual_address: IndividualAddressableType) -> None:
    """
    Restart a device, opening and closing a connection to it.

    :param xknx: the XKNX object
    :param individual_address: address of the device to restart
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        await dm_restart_r_co(conn)
