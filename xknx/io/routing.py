"""
Abstraction for handling KNX/IP routing.

Routing uses UDP Multicast to broadcast and receive KNX/IP messages.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

from xknx.core import XknxConnectionState
from xknx.knxip import (
    HPAI,
    CEMIFrame,
    CEMIMessageCode,
    KNXIPFrame,
    KNXIPServiceType,
    RoutingIndication,
)
from xknx.telegram import TelegramDirection

from .interface import Interface
from .udp_client import UDPClient

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

    TelegramCallbackType = Callable[[Telegram], None]

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

        self.udpclient = UDPClient(
            self.xknx,
            (local_ip, 0),
            (self.xknx.multicast_group, self.xknx.multicast_port),
            multicast=True,
        )

        self.udpclient.register_callback(
            self.response_rec_callback, [KNXIPServiceType.ROUTING_INDICATION]
        )

    def response_rec_callback(
        self, knxipframe: KNXIPFrame, source: HPAI, _: UDPClient
    ) -> None:
        """Verify and handle knxipframe. Callback from internal udpclient."""
        if not isinstance(knxipframe.body, RoutingIndication):
            logger.warning("Service type not implemented: %s", knxipframe)
        elif knxipframe.body.cemi is None:
            # ignore unsupported CEMI frame
            return
        elif knxipframe.body.cemi.src_addr == self.xknx.own_address:
            logger.debug("Ignoring own packet")
        else:
            telegram = knxipframe.body.cemi.telegram
            telegram.direction = TelegramDirection.INCOMING

            if self.telegram_received_callback is not None:
                self.telegram_received_callback(telegram)

    async def send_telegram(self, telegram: "Telegram") -> None:
        """Send Telegram to routing connected device."""
        cemi = CEMIFrame.init_from_telegram(
            self.xknx,
            telegram=telegram,
            code=CEMIMessageCode.L_DATA_IND,
            src_addr=self.xknx.own_address,
        )
        routing_indication = RoutingIndication(self.xknx, cemi=cemi)
        await self.send_knxipframe(KNXIPFrame.init_from_body(routing_indication))

    async def send_knxipframe(self, knxipframe: KNXIPFrame) -> None:
        """Send KNXIPFrame to connected routing device."""
        self.udpclient.send(knxipframe)

    async def connect(self) -> bool:
        """Start routing."""
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        try:
            await self.udpclient.connect()
        except OSError as ex:
            logger.debug(
                "Could not establish connection to KNX/IP network. %s: %s",
                type(ex).__name__,
                ex,
            )
            await self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
            # close udp client to prevent open file descriptors
            await self.udpclient.stop()
            raise ex
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        return True

    async def disconnect(self) -> None:
        """Stop routing."""
        await self.udpclient.stop()
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
