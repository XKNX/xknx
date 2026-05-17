"""DM_Restart_RCo — KNX 03.05.02 §3.7.3."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.telegram import Telegram, apci, tpci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def dm_restart(xknx: XKNX, individual_address: IndividualAddressableType) -> None:
    """
    Restart the device.

    :param xknx: XKNX object
    :param individual_address: address of device to reset
    """
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
