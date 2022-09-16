"""
Abstraction for handling KNX/IP routing.

Routing uses UDP Multicast to broadcast and receive KNX/IP messages.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import random
import time
from typing import TYPE_CHECKING

from xknx.core import XknxConnectionState
from xknx.exceptions import CommunicationError
from xknx.knxip import (
    HPAI,
    CEMIFrame,
    CEMIMessageCode,
    KNXIPFrame,
    KNXIPServiceType,
    RoutingBusy,
    RoutingIndication,
)
from xknx.telegram import TelegramDirection

from .interface import Interface, TelegramCallbackType
from .transport import KNXIPTransport, UDPTransport

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class _RoutingFlowControl:
    """
    Class for hanling KNX/IP routing flow control.

    See KNX Specifications 3.8.5 Routing §2.3.5 Flow control handling
    """

    def __init__(self) -> None:
        self._busy_start_time: float | None = None
        self._last_busy_frame_time: float = 0.0
        self._ready = asyncio.Event()
        self._ready.set()
        self._received_busy_frames: int = 0
        self._timer_task: asyncio.Task[None] | None = None
        self._wait_time_ms: int = 0

    def cancel(self) -> None:
        """Cancel internal tasks."""
        if self._timer_task:
            self._timer_task.cancel()

    @asynccontextmanager
    async def throttle(self) -> AsyncIterator[None]:
        """Context manager to wait for ready state and throttle outgoing frames."""
        await self._ready.wait()
        yield
        # limit RoutingIndication transmission rate according to
        # KNX Specifications 3.2.6 Communication Medium KNX IP §2.1
        # simplified version - pause 20 ms after transmit a RoutingIndication
        await asyncio.sleep(0.02)

    def handle_routing_busy(self, routing_busy: RoutingBusy) -> None:
        """Handle incoming RoutingBusy."""
        self._ready.clear()
        now = time.monotonic()
        logger.warning(
            "RoutingBusy received: %s - %s in moving time window",
            routing_busy,
            self._received_busy_frames + 1,
        )
        if self._busy_start_time is not None:
            # only apply if we have already received a RoutingBusy frame and are still pausing
            if (now - self._last_busy_frame_time) > 0.01:
                self._received_busy_frames += 1
            remaining_ms = (now - self._busy_start_time) * 1000
            if remaining_ms >= routing_busy.wait_time:
                return
        self._wait_time_ms = routing_busy.wait_time
        self._busy_start_time = now

        if self._timer_task:
            self._timer_task.cancel()
        self._timer_task = asyncio.create_task(self._resume_sending())

    async def _resume_sending(self) -> None:
        """Reset ready flag after wait_time_ms and fade out slowduration."""
        random_wait_extension_ms = random.random() * self._received_busy_frames * 50
        slowduration_ms = self._received_busy_frames * 100
        await asyncio.sleep((self._wait_time_ms + random_wait_extension_ms) / 1000)

        self._ready.set()
        self._busy_start_time = None
        await asyncio.sleep(slowduration_ms / 1000)
        while self._received_busy_frames > 0:
            await asyncio.sleep(5 / 1000)
            self._received_busy_frames -= 1


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
            self._handle_frame,
            [
                KNXIPServiceType.ROUTING_INDICATION,
                KNXIPServiceType.ROUTING_BUSY,
            ],
        )
        self._flow_control = _RoutingFlowControl()

    ####################
    #
    # CONNECT DISCONNECT
    #
    ####################

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
        self._flow_control.cancel()

    ##################
    #
    # OUTGOING FRAMES
    #
    ##################

    async def send_telegram(self, telegram: "Telegram") -> None:
        """Send Telegram to routing connected device."""
        cemi = CEMIFrame.init_from_telegram(
            telegram=telegram,
            code=CEMIMessageCode.L_DATA_IND,
            src_addr=self.xknx.own_address,
        )
        routing_indication = RoutingIndication(cemi=cemi)

        async with self._flow_control.throttle():
            self._send_knxipframe(KNXIPFrame.init_from_body(routing_indication))

    def _send_knxipframe(self, knxipframe: KNXIPFrame) -> None:
        """Send KNXIPFrame to connected routing device."""
        self.udp_transport.send(knxipframe)

    ##################
    #
    # INCOMING FRAMES
    #
    ##################

    def _handle_frame(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Handle incoming KNXIPFrames. Callback from internal udp_transport."""
        if isinstance(knxipframe.body, RoutingIndication):
            self._handle_routing_indication(knxipframe.body)
        elif isinstance(knxipframe.body, RoutingBusy):
            self._flow_control.handle_routing_busy(knxipframe.body)
        else:
            logger.warning("Service not implemented: %s", knxipframe)

    def _handle_routing_indication(self, routing_indication: RoutingIndication) -> None:
        """Handle incoming RoutingIndication."""
        if routing_indication.cemi is None:
            # Don't handle invalid cemi frames (None)
            return
        if routing_indication.cemi.src_addr == self.xknx.own_address:
            logger.debug("Ignoring own packet")
            return

        # TODO: is cemi message code L_DATA.req or .con valid for routing? if not maybe warn and ignore
        asyncio.create_task(self.handle_cemi_frame(routing_indication.cemi))

    async def handle_cemi_frame(self, cemi: CEMIFrame) -> None:
        """Handle incoming telegram and send responses if applicable (device management)."""
        telegram = cemi.telegram
        telegram.direction = TelegramDirection.INCOMING

        if response_tgs := await self.telegram_received_callback(telegram):
            for response in response_tgs:
                await self.send_telegram(response)
