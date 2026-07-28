"""DM_Restart_RCo — KNX 03.05.02 §3.7.3."""

from __future__ import annotations

import logging

from xknx.management.management import Management, P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

logger = logging.getLogger("xknx.management.procedures")


async def dm_restart_r_co(conn: P2PConnection) -> None:
    """
    Restart the device on an already-open connection.

    :param conn: an established P2P connection to the device
    """
    logger.debug("Requesting a Basic Restart of %s.", conn.address)
    await conn.send_data_no_ack(apci.Restart())


async def dm_restart(
    management: Management, individual_address: IndividualAddressableType
) -> None:
    """
    Restart a device, opening and closing a connection to it.

    :param management: connection manager used to open a P2P connection
    :param individual_address: address of the device to restart
    """
    async with management.connection(IndividualAddress(individual_address)) as conn:
        await dm_restart_r_co(conn)
