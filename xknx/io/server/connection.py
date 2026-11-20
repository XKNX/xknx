"""
The communication channels of a KNXnet/IP tunnelling server.

A `ServerConnection` is one channel opened by a CONNECT_REQUEST: a tunnel or a
device management connection. It tracks the sequence counters, the heartbeat
timeout and sends the server's own requests - TUNNELLING_REQUEST, the Tunnelling
Feature services, DEVICE_CONFIGURATION_REQUEST - one at a time, waiting for the
acknowledgement over UDP.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Final

from xknx.io.const import (
    DEVICE_CONFIGURATION_REQUEST_REPETITIONS,
    DEVICE_CONFIGURATION_REQUEST_TIMEOUT,
)
from xknx.io.data_connection import IncomingSequenceCounter
from xknx.knxip import (
    ConnectRequestType,
    ErrorCode,
    HostProtocol,
    KNXIPBody,
    KNXIPFrame,
    TunnellingLayer,
)
from xknx.telegram import IndividualAddress

logger = logging.getLogger("xknx.log")

# A TUNNELLING_REQUEST is repeated once when it isn't acknowledged within one
# second, then the connection is terminated - KNX v01.07.01 - Tunnelling 03.08.04 -
# §2.6.1. The Tunnelling Feature services follow the same rules (§3.1).
TUNNELLING_REQUEST_TIMEOUT: Final = 1.0
TUNNELLING_REQUEST_REPETITIONS: Final = 1


class Peer(ABC):
    """Where the server sends frames to: a UDP endpoint or a TCP connection."""

    protocol: HostProtocol

    @abstractmethod
    def send(self, knxipframe: KNXIPFrame) -> None:
        """Send a KNX/IP frame."""

    @property
    @abstractmethod
    def address(self) -> tuple[str, int]:
        """Return the IP address and port of the other end."""


@dataclass(frozen=True, slots=True)
class TunnelInfo:
    """An open tunnel of a `KNXIPTunnellingServer`."""

    communication_channel: int
    individual_address: IndividualAddress
    client: tuple[str, int]
    protocol: HostProtocol
    layer: TunnellingLayer


class ServerConnection:
    """A communication channel of the server - a tunnel or a device management connection."""

    __slots__ = (
        "_heartbeat_handle",
        "_heartbeat_timeout",
        "_on_failure",
        "_outgoing",
        "_pending_ack",
        "_sender",
        "communication_channel",
        "connection_type",
        "control_peer",
        "data_peer",
        "feature_info_enabled",
        "individual_address",
        "layer",
        "local_ip",
        "sequence_in",
        "sequence_out",
    )

    def __init__(
        self,
        communication_channel: int,
        connection_type: ConnectRequestType,
        control_peer: Peer,
        data_peer: Peer,
        local_ip: str,
        heartbeat_timeout: float,
        on_failure: Callable[[ServerConnection], None],
        individual_address: IndividualAddress | None = None,
        layer: TunnellingLayer = TunnellingLayer.DATA_LINK_LAYER,
    ) -> None:
        """
        Initialize ServerConnection class.

        `on_failure` is called when the heartbeat times out or a request of the
        server stays unacknowledged; it shall terminate the connection.
        """
        self.communication_channel = communication_channel
        self.connection_type = connection_type
        self.control_peer = control_peer
        self.data_peer = data_peer
        self.local_ip = local_ip
        self.individual_address = individual_address
        self.layer = layer
        self.sequence_in = IncomingSequenceCounter()
        self.sequence_out = 0
        # Interface Feature 08 "Interface Feature Info service Enable" is disabled
        # for every new connection - KNX v01.07.01 - Tunnelling 03.08.04 - §3.6.9
        self.feature_info_enabled = False
        self._heartbeat_timeout = heartbeat_timeout
        self._on_failure = on_failure
        self._heartbeat_handle: asyncio.TimerHandle | None = None
        self._outgoing: asyncio.Queue[Callable[[int], KNXIPBody]] = asyncio.Queue()
        self._pending_ack: tuple[int, asyncio.Future[ErrorCode]] | None = None
        self._sender: asyncio.Task[None] | None = None

    @property
    def tcp(self) -> bool:
        """Return whether the connection runs over TCP."""
        return self.data_peer.protocol is HostProtocol.IPV4_TCP

    @property
    def is_tunnel(self) -> bool:
        """Return whether the connection is a tunnel."""
        return self.connection_type is ConnectRequestType.TUNNEL_CONNECTION

    def start(self) -> None:
        """Start the heartbeat timeout and the sender of the server's requests."""
        self.alive()
        self._sender = asyncio.create_task(
            self._send_requests(),
            name=f"KNXnet/IP server channel {self.communication_channel}",
        )

    def stop(self) -> None:
        """Stop the heartbeat timeout and the sender - the connection is closed."""
        if self._heartbeat_handle is not None:
            self._heartbeat_handle.cancel()
            self._heartbeat_handle = None
        if self._sender is not None:
            if self._sender is not asyncio.current_task():
                self._sender.cancel()
            self._sender = None

    def alive(self) -> None:
        """
        Restart the heartbeat timeout after a correctly received frame.

        Without a frame for `heartbeat_timeout` (120 s) the server terminates the
        connection - KNX v01.06.02 - Core 03.08.02 - §5.4.
        """
        if self._heartbeat_handle is not None:
            self._heartbeat_handle.cancel()
        self._heartbeat_handle = asyncio.get_running_loop().call_later(
            self._heartbeat_timeout, self._heartbeat_expired
        )

    def _heartbeat_expired(self) -> None:
        """Terminate the connection after the heartbeat timeout. Callback."""
        self._heartbeat_handle = None
        logger.info(
            "KNXnet/IP server: no heartbeat from channel %s within %s seconds",
            self.communication_channel,
            self._heartbeat_timeout,
        )
        self._on_failure(self)

    def send_request(self, body: Callable[[int], KNXIPBody]) -> None:
        """Queue a request of the server; `body` builds it for a sequence counter."""
        self._outgoing.put_nowait(body)

    def ack_received(self, sequence_counter: int, status_code: ErrorCode) -> None:
        """Resolve the request waiting for this TUNNELLING_ACK or DEVICE_CONFIGURATION_ACK."""
        if self._pending_ack is None:
            return
        pending_sequence, future = self._pending_ack
        if sequence_counter == pending_sequence and not future.done():
            future.set_result(status_code)

    async def _send_requests(self) -> None:
        """Send the queued requests one after another. Worker task."""
        if self.is_tunnel:
            timeout = TUNNELLING_REQUEST_TIMEOUT
            repetitions = TUNNELLING_REQUEST_REPETITIONS
        else:
            # KNX v01.07.03 - Device Management 03.08.03 - §2.3.2
            timeout = DEVICE_CONFIGURATION_REQUEST_TIMEOUT
            repetitions = DEVICE_CONFIGURATION_REQUEST_REPETITIONS
        while True:
            body = await self._outgoing.get()
            knxipframe = KNXIPFrame.init_from_body(body(self.sequence_out))
            if self.tcp:
                # no acknowledgement on TCP - KNX v01.07.01 - Tunnelling 03.08.04 - §2.6.2
                self.data_peer.send(knxipframe)
                self.sequence_out = self.sequence_out + 1 & 0xFF
                continue
            if not await self._send_acknowledged(knxipframe, timeout, repetitions):
                logger.info(
                    "KNXnet/IP server: request on channel %s was not acknowledged",
                    self.communication_channel,
                )
                self._on_failure(self)
                return
            self.sequence_out = self.sequence_out + 1 & 0xFF

    async def _send_acknowledged(
        self, knxipframe: KNXIPFrame, timeout: float, repetitions: int
    ) -> bool:
        """Send a frame, repeating it with the same sequence counter until it is acknowledged."""
        for _attempt in range(repetitions + 1):
            future: asyncio.Future[ErrorCode] = (
                asyncio.get_running_loop().create_future()
            )
            self._pending_ack = (self.sequence_out, future)
            self.data_peer.send(knxipframe)
            try:
                async with asyncio.timeout(timeout):
                    status_code = await future
            except TimeoutError:
                continue
            finally:
                self._pending_ack = None
            if status_code is ErrorCode.E_NO_ERROR:
                return True
        return False

    def info(self) -> TunnelInfo:
        """Return what describes the tunnel."""
        assert self.individual_address is not None
        return TunnelInfo(
            communication_channel=self.communication_channel,
            individual_address=self.individual_address,
            client=self.data_peer.address,
            protocol=self.data_peer.protocol,
            layer=self.layer,
        )
