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
    CouldNotParseCEMI,
    DataSecureError,
    UnsupportedCEMIMessage,
)
from xknx.secure.data_secure import DataSecure
from xknx.secure.keyring import Keyring
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, tpci
from xknx.util import asyncio_timeout

from .cemi_frame import CEMIFrame, CEMILData
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
        cemi_data = CEMILData.init_from_telegram(
            telegram=telegram,
            src_addr=(
                self.xknx.current_address if telegram.source_address.raw == 0 else None
            ),
        )
        cemi = CEMIFrame(
            code=CEMIMessageCode.L_DATA_REQ,
            data=cemi_data,
        )

        logger.debug("Outgoing CEMI: %s", cemi)
        if self.data_secure is not None:
            cemi.data = self.data_secure.outgoing_cemi(cemi_data=cemi_data)
        self._l_data_confirmation_event.clear()
        try:
            await self.xknx.knxip_interface.send_cemi(cemi)
        except (ConversionError, CommunicationError) as ex:
            logger.warning("Could not send CEMI frame: %s for %s", ex, cemi)
            self.xknx.connection_manager.cemi_count_outgoing_error += 1
            raise ex

        try:
            async with asyncio_timeout(REQUEST_TO_CONFIRMATION_TIMEOUT):
                await self._l_data_confirmation_event.wait()
        except asyncio.TimeoutError:
            self.xknx.connection_manager.cemi_count_outgoing_error += 1
            raise ConfirmationError(
                f"L_DATA_CON Data Link Layer confirmation timed out for {cemi}"
            )
        self.xknx.connection_manager.cemi_count_outgoing += 1

    def handle_raw_cemi(self, raw_cemi: bytes) -> None:
        """Parse and handle incoming raw CEMI Frames."""
        try:
            cemi = CEMIFrame.from_knx(raw_cemi)
        except CouldNotParseCEMI as cemi_parse_err:
            logger.warning("CEMI Frame failed to parse: %s", cemi_parse_err)
            self.xknx.connection_manager.cemi_count_incoming_error += 1
            return
        except UnsupportedCEMIMessage as unsupported_cemi_err:
            logger.info("CEMI not supported: %s", unsupported_cemi_err)
            self.xknx.connection_manager.cemi_count_incoming_error += 1
            return
        self.handle_cemi_frame(cemi)

    def handle_cemi_frame(self, cemi: CEMIFrame) -> None:
        """Handle incoming CEMI Frames."""
        if not isinstance(cemi.data, CEMILData):
            logger.debug("Ignoring incoming non-link-layer CEMI: %s", cemi)
            return

        if cemi.code is CEMIMessageCode.L_DATA_CON:
            # L_DATA_CON confirmation frame signals ready to send next telegram
            self._l_data_confirmation_event.set()
            logger.debug("Incoming CEMI confirmation: %s", cemi)
            return
        if cemi.code is CEMIMessageCode.L_DATA_REQ:
            # L_DATA_REQ frames should only be outgoing.
            logger.warning("Received unexpected L_DATA_REQ frame: %s", cemi)
            self.xknx.connection_manager.cemi_count_incoming_error += 1
            return
        logger.debug("Incoming CEMI: %s", cemi)

        if self.data_secure is not None:
            try:
                cemi.data = self.data_secure.received_cemi(cemi_data=cemi.data)
            except DataSecureError as err:
                data_secure_logger.log(
                    err.log_level,
                    "Could not decrypt CEMI frame: %s",
                    err,
                )
                return
        self.xknx.connection_manager.cemi_count_incoming += 1
        telegram = cemi.data.telegram()
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
