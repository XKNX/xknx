"""
CEMI Frame handler.

This class represents a CEMI Client vaguely according to KNX specification 3/6/3 §4.1.2.
It is responsible for sending and receiving CEMI frames to/from a CEMI Server - this
can be a remote server when using IP tunnelling or a local server when using IP routing.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from xknx.exceptions import (
    CommunicationError,
    ConfirmationError,
    ConversionError,
    DataSecureError,
)
from xknx.secure.data_secure import DataSecure
from xknx.secure.keyring import Keyring
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, tpci

from .cemi_frame import CEMIFrame
from .const import CEMIMessageCode

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.cemi")
data_secure_logger = logging.getLogger("xknx.data_secure")

# See 3/6/3 EMI_IMI §4.1.5 Data Link Layer messages
REQUEST_TO_CONFIRMATION_TIMEOUT = 3


class CEMIHandler:
    """Class for handling CEMI frames from/to the TelegramQueue."""

    def __init__(self, xknx: XKNX) -> None:
        """Initialize CEMIHandler class."""
        self.xknx = xknx
        self.data_secure: DataSecure | None = None
        self._l_data_confirmation_event = asyncio.Event()

    def data_secure_init(self, keyring: Keyring | None) -> None:
        """Initialize DataSecure."""
        if keyring is None:
            self.data_secure = None
        else:
            self.data_secure = DataSecure.init_from_keyring(keyring)

    async def send_telegram(self, telegram: Telegram) -> None:
        """Create a CEMIFrame from a Telegram and send it to the CEMI Server."""
        cemi = CEMIFrame.init_from_telegram(
            telegram=telegram,
            code=CEMIMessageCode.L_DATA_REQ,
            src_addr=(
                self.xknx.current_address if telegram.source_address.raw == 0 else None
            ),
        )
        logger.debug("Outgoing CEMI: %s", cemi)
        if self.data_secure is not None:
            cemi = self.data_secure.outgoing_cemi(cemi=cemi)

        self._l_data_confirmation_event.clear()
        try:
            await self.xknx.knxip_interface.send_cemi(cemi)
        except (ConversionError, CommunicationError) as ex:
            logger.warning("Could not send CEMI frame: %s for %s", ex, cemi)
            raise ex

        try:
            await asyncio.wait_for(
                self._l_data_confirmation_event.wait(),
                timeout=REQUEST_TO_CONFIRMATION_TIMEOUT,
            )
        except asyncio.TimeoutError:
            raise ConfirmationError(
                f"L_DATA_CON Data Link Layer confirmation timed out for {cemi}"
            )

    def handle_cemi_frame(self, cemi: CEMIFrame) -> None:
        """Parse and handle incoming CEMI Frames."""
        logger.debug("Incoming CEMI: %s", cemi)

        if cemi.code is CEMIMessageCode.L_DATA_CON:
            # L_DATA_CON confirmation frame signals ready to send next telegram
            self._l_data_confirmation_event.set()
            return
        if cemi.code is CEMIMessageCode.L_DATA_REQ:
            # L_DATA_REQ frames should only be outgoing.
            logger.warning("Received unexpected L_DATA_REQ frame: %s", cemi)
            return

        # TODO: do we have to decrypt Data Secure L_DATA_CON?
        if self.data_secure is not None:
            try:
                cemi = self.data_secure.received_cemi(cemi=cemi)
            except DataSecureError as err:
                data_secure_logger.warning("Could not decrypt CEMI frame: %s", err)
                return
        # TODO: remove telegram init from CEMIFrame class and move it here?
        telegram = cemi.telegram
        telegram.direction = TelegramDirection.INCOMING
        self.telegram_received(telegram)

    def telegram_received(self, telegram: Telegram) -> None:
        """Forward Telegram to upper layer."""
        if isinstance(telegram.tpci, tpci.TDataGroup):
            self.xknx.telegrams.put_nowait(telegram)
            return
        if (
            isinstance(telegram.destination_address, IndividualAddress)
            and telegram.destination_address != self.xknx.current_address
        ):
            return
        self.xknx.management.process(telegram)
