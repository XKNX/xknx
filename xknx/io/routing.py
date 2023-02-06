"""
Abstraction for handling KNXnet/IP routing.

Routing uses UDP Multicast to send and receive KNXnet/IP messages.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
import random
from typing import TYPE_CHECKING, Final

from xknx.cemi import CEMIFrame, CEMIMessageCode
from xknx.core import XknxConnectionState
from xknx.exceptions import CommunicationError, UnsupportedCEMIMessage
from xknx.knxip import (
    HPAI,
    KNXIPFrame,
    KNXIPServiceType,
    RoutingBusy,
    RoutingIndication,
    RoutingLostMessage,
)
from xknx.telegram import IndividualAddress

from .const import DEFAULT_INDIVIDUAL_ADDRESS, DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from .interface import CEMICallbackType, Interface
from .ip_secure import SecureGroup
from .transport import KNXIPTransport, UDPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")
cemi_logger = logging.getLogger("xknx.cemi")

BUSY_DECREMENT_TIME: Final = 0.005  # 5 ms
BUSY_INCREMENT_COOLDOWN: Final = 0.01  # 10 ms
BUSY_RANDOM_TIME_FACTOR: Final = 0.05  # 50 ms
BUSY_SLOWDURATION_TIME_FACTOR: Final = 0.1  # 100 ms
ROUTING_INDICATION_WAIT_TIME: Final = 0.02  # 20 ms

DEFAULT_LATENCY_TOLERANCE_MS: Final = 1000


class _RoutingFlowControl:
    """
    Class for handling KNXnet/IP routing flow control.

    See KNX Specifications 3.8.5 Routing §2.3.5 Flow control handling
    """

    def __init__(self) -> None:
        self._last_busy_frame_time: float = 0.0
        self._last_sent_routing_indication_time: float = 0.0
        self._loop = asyncio.get_running_loop()
        self._ready = asyncio.Event()
        self._ready.set()
        self._received_busy_frames: int = 0
        self._timer_task: asyncio.Task[None] | None = None
        self._wait_start_time: float | None = None
        self._wait_time_ms: int = 0

    def cancel(self) -> None:
        """Cancel internal tasks."""
        if self._timer_task:
            self._timer_task.cancel()

    @asynccontextmanager
    async def throttle(self) -> AsyncIterator[None]:
        """Context manager to wait for ready state and throttle outgoing frames."""
        # limit RoutingIndication transmission rate according to
        # KNX Specifications 3.2.6 Communication Medium KNX IP §2.1
        # simplified version - pause 20 ms after transmit a RoutingIndication
        elapsed = self._loop.time() - self._last_sent_routing_indication_time
        if elapsed < ROUTING_INDICATION_WAIT_TIME:
            await asyncio.sleep(ROUTING_INDICATION_WAIT_TIME - elapsed)

        await self._ready.wait()
        yield
        self._last_sent_routing_indication_time = self._loop.time()

    def handle_routing_busy(self, routing_busy: RoutingBusy) -> None:
        """Handle incoming RoutingBusy."""
        self._ready.clear()
        now = self._loop.time()
        previous_busy_frame_time = self._last_busy_frame_time
        self._last_busy_frame_time = now
        if self._wait_start_time is None:
            logger.info(
                "RoutingBusy received: %s",
                routing_busy,
            )
        else:
            # only apply if we have already received a RoutingBusy frame and are still pausing
            if (now - previous_busy_frame_time) > BUSY_INCREMENT_COOLDOWN:
                self._received_busy_frames += 1
            logger.debug(
                "RoutingBusy received: %s - %s ms since previous - number %s in moving time window",
                routing_busy,
                round((now - previous_busy_frame_time) * 1000),
                self._received_busy_frames,
            )
            # discard frame if wait time is lower than remaining time
            remaining_ms = (now - self._wait_start_time) * 1000
            if remaining_ms >= routing_busy.wait_time:
                return
        self._wait_time_ms = routing_busy.wait_time
        self._wait_start_time = now

        if self._timer_task:
            self._timer_task.cancel()
        self._timer_task = asyncio.create_task(self._resume_sending())

    async def _resume_sending(self) -> None:
        """Reset ready flag after wait_time_ms and fade out slowduration."""
        random_wait_extension = (
            random.random() * self._received_busy_frames * BUSY_RANDOM_TIME_FACTOR
        )
        slowduration = self._received_busy_frames * BUSY_SLOWDURATION_TIME_FACTOR
        await asyncio.sleep(self._wait_time_ms / 1000 + random_wait_extension)

        self._ready.set()
        self._wait_start_time = None
        await asyncio.sleep(slowduration)
        while self._received_busy_frames > 0:
            await asyncio.sleep(BUSY_DECREMENT_TIME)
            self._received_busy_frames -= 1


class Routing(Interface):
    """Class for handling KNXnet/IP multicast communication."""

    transport: UDPTransport

    def __init__(
        self,
        xknx: XKNX,
        individual_address: IndividualAddress | None,
        cemi_received_callback: CEMICallbackType,
        local_ip: str,
        multicast_group: str = DEFAULT_MCAST_GRP,
        multicast_port: int = DEFAULT_MCAST_PORT,
    ):
        """Initialize Routing class."""
        self.xknx = xknx
        self.individual_address = individual_address or DEFAULT_INDIVIDUAL_ADDRESS
        self.cemi_received_callback = cemi_received_callback
        self.local_ip = local_ip
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port

        self._init_transport()
        self.transport.register_callback(
            self._handle_frame,
            [
                KNXIPServiceType.ROUTING_INDICATION,
                KNXIPServiceType.ROUTING_BUSY,
                KNXIPServiceType.ROUTING_LOST_MESSAGE,
            ],
        )
        self._flow_control = _RoutingFlowControl()

    def _init_transport(self) -> None:
        """Initialize transport."""
        self.transport = UDPTransport(
            local_addr=(self.local_ip, 0),
            remote_addr=(self.multicast_group, self.multicast_port),
            multicast=True,
        )

    ####################
    #
    # CONNECT DISCONNECT
    #
    ####################

    async def connect(self) -> bool:
        """Start routing."""
        self.xknx.current_address = self.individual_address
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTING
        )
        try:
            await self.transport.connect()
        except OSError as ex:
            logger.debug(
                "Could not establish connection to KNXnet/IP network. %s: %s",
                type(ex).__name__,
                ex,
            )
            await self.xknx.connection_manager.connection_state_changed(
                XknxConnectionState.DISCONNECTED
            )
            # close udp transport to prevent open file descriptors
            self.transport.stop()
            raise CommunicationError("Routing could not be started") from ex
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        return True

    async def disconnect(self) -> None:
        """Stop routing."""
        self.transport.stop()
        await self.xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        self._flow_control.cancel()

    ##################
    #
    # OUTGOING FRAMES
    #
    ##################

    async def send_cemi(self, cemi: CEMIFrame) -> None:
        """Send CEMIFrame to the network."""
        # send L_DATA_IND to network, create L_DATA_CON locally for routing
        cemi.code = CEMIMessageCode.L_DATA_IND
        routing_indication = RoutingIndication(raw_cemi=cemi.to_knx())

        async with self._flow_control.throttle():
            self._send_knxipframe(KNXIPFrame.init_from_body(routing_indication))

        cemi.code = CEMIMessageCode.L_DATA_CON
        self.cemi_received_callback(cemi)

    def _send_knxipframe(self, knxipframe: KNXIPFrame) -> None:
        """Send KNXIPFrame to connected routing device."""
        self.transport.send(knxipframe)

    ##################
    #
    # INCOMING FRAMES
    #
    ##################

    def _handle_frame(
        self, knxipframe: KNXIPFrame, source: HPAI, _: KNXIPTransport
    ) -> None:
        """Handle incoming KNXIPFrames. Callback from internal transport."""
        if isinstance(knxipframe.body, RoutingIndication):
            self._handle_routing_indication(knxipframe.body)
        elif isinstance(knxipframe.body, RoutingBusy):
            self._flow_control.handle_routing_busy(knxipframe.body)
        elif isinstance(knxipframe.body, RoutingLostMessage):
            logger.warning(
                "RoutingLostMessage received from %s - %s lost messages.",
                source.ip_addr,
                knxipframe.body.lost_messages,
            )
        else:
            logger.warning("Service not implemented: %s", knxipframe)

    def _handle_routing_indication(self, routing_indication: RoutingIndication) -> None:
        """Handle incoming RoutingIndication."""
        try:
            cemi = CEMIFrame.from_knx(routing_indication.raw_cemi)
        except UnsupportedCEMIMessage as unsupported_cemi_err:
            logger.warning("CEMI not supported: %s", unsupported_cemi_err)
            return
        if cemi.src_addr == self.individual_address:
            logger.debug("Ignoring own packet %s", cemi)
            return
        self.cemi_received_callback(cemi)


class SecureRouting(Routing):
    """Class for handling KNXnet/IP secure multicast communication."""

    transport: SecureGroup

    def __init__(
        self,
        xknx: XKNX,
        individual_address: IndividualAddress | None,
        cemi_received_callback: CEMICallbackType,
        local_ip: str,
        backbone_key: bytes,
        latency_ms: int | None = None,
        multicast_group: str = DEFAULT_MCAST_GRP,
        multicast_port: int = DEFAULT_MCAST_PORT,
    ):
        """Initialize SecureRouting class."""
        self.backbone_key = backbone_key
        self.latency_ms = latency_ms or DEFAULT_LATENCY_TOLERANCE_MS
        super().__init__(
            xknx,
            individual_address=individual_address,
            cemi_received_callback=cemi_received_callback,
            local_ip=local_ip,
            multicast_group=multicast_group,
            multicast_port=multicast_port,
        )

    def _init_transport(self) -> None:
        """Initialize transport."""
        self.transport = SecureGroup(
            local_addr=(self.local_ip, 0),
            remote_addr=(self.multicast_group, self.multicast_port),
            backbone_key=self.backbone_key,
            latency_ms=self.latency_ms,
        )
