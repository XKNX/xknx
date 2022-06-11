"""
Abstraction for handling KNX/IP routing.

Routing uses UDP Multicast to broadcast and receive KNX/IP messages.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from xknx.core import XknxConnectionState
from xknx.exceptions import CommunicationError
from xknx.knxip import (
    HPAI,
    CEMIFrame,
    CEMIMessageCode,
    KNXIPFrame,
    KNXIPServiceType,
    RoutingIndication,
)
from xknx.telegram import TelegramDirection

from .interface import Interface, TelegramCallbackType
from .transport import KNXIPTransport, UDPTransport

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Routing(Interface):
    """Class for handling KNX/IP routing."""

    def __init__(
        self,
        xknx: XKNX,
        telegram_received_callback: TelegramCallbackType,
        local_ip: str,
    ):
        """Initialize Routing class."""
        self.xknx = xknx
        self.telegram_received_callback = telegram_received_callback
        self.local_ip = local_ip

        self.udp_transport = UDPTransport(
            local_addr=(local_ip, 0),
            remote_addr=(self.xknx.multicast_group, self.xknx.multicast_port),
            multicast=True,
        )

        self.udp_transport.register_callback(
            self.response_rec_callback, [KNXIPServiceType.ROUTING_INDICATION]
        )

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Verify and handle knxipframe. Callback from internal udp_transport."""
        if not isinstance(knxipframe.body, RoutingIndication):
            logger.warning("Service type not implemented: %s", knxipframe)
        elif knxipframe.body.cemi is None:
            # ignore unsupported CEMI frame
            return
        elif knxipframe.body.cemi.src_addr == self.xknx.own_address:
            logger.debug("Ignoring own packet")
        else:
            # TODO: is cemi message code L_DATA.req or .con valid for routing? if not maybe warn and ignore
            asyncio.create_task(self.handle_cemi_frame(knxipframe.body.cemi))

    async def handle_cemi_frame(self, cemi: CEMIFrame) -> None:
        """Handle incoming telegram and send responses if applicable (device management)."""
        telegram = cemi.telegram
        telegram.direction = TelegramDirection.INCOMING

        if response_tgs := await self.telegram_received_callback(telegram):
            for response in response_tgs:
                await self.send_telegram(response)

    async def send_telegram(self, telegram: "Telegram") -> None:
        """Send Telegram to routing connected device."""
        cemi = CEMIFrame.init_from_telegram(
            telegram=telegram,
            code=CEMIMessageCode.L_DATA_IND,
            src_addr=self.xknx.own_address,
        )
        routing_indication = RoutingIndication(cemi=cemi)
        await self.send_knxipframe(KNXIPFrame.init_from_body(routing_indication))

    async def send_knxipframe(self, knxipframe: KNXIPFrame) -> None:
        """Send KNXIPFrame to connected routing device."""
        self.udp_transport.send(knxipframe)

    async def connect(self) -> bool:
        """Start routing."""
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        try:
            await self.udp_transport.connect()
        except OSError as ex:
            logger.debug(
                "Could not establish connection to KNX/IP network. %s: %s",
                type(ex).__name__,
                ex,
            )
            await self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
            # close udp transport to prevent open file descriptors
            self.udp_transport.stop()
            raise CommunicationError("Routing could not be started") from ex
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        return True

    async def disconnect(self) -> None:
        """Stop routing."""
        self.udp_transport.stop()
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
