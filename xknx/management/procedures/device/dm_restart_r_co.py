"""DM_Restart_RCo — KNX 03.05.02 §3.7.3."""

from __future__ import annotations

import logging

from xknx.management.protocols import P2PConnection
from xknx.telegram import apci

logger = logging.getLogger("xknx.management.procedures")


async def dm_restart(conn: P2PConnection) -> None:
    """
    Restart the device on an already-open connection.

    :param conn: an established P2P connection to the device
    """
    logger.debug("Requesting a Basic Restart of %s.", conn.address)
    await conn.send_data_no_ack(apci.Restart())
