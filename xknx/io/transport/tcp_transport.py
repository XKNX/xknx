"""
TCPTransport is an abstraction for handling the complete TCP io.

The module is build upon asyncio stream socket functions.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Callable

from xknx.exceptions import CommunicationError, CouldNotParseKNXIP, IncompleteKNXIPFrame
from xknx.knxip import HPAI, HostProtocol, KNXIPFrame

from .ip_transport import KNXIPTransport

raw_socket_logger = logging.getLogger("xknx.raw_socket")
logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")


class TCPTransport(KNXIPTransport):
    """Class for handling (sending and receiving) TCP packets."""

    class TCPTransportFactory(asyncio.Protocol):
        """Abstraction for managing the asyncio-tcp protocol."""

        def __init__(
            self,
            data_received_callback: Callable[[bytes], None],
            connection_lost_callback: Callable[[], None],
        ):
            """Initialize UDPTransportFactory class."""
            self.transport: asyncio.BaseTransport | None = None
            self.data_received_callback = data_received_callback
            self.connection_lost_callback = connection_lost_callback

            # Workaround for issue of TCP Transport in ProactorEventLoop in py3.10 and py3.11
            # on Windows returning bytearray instead of bytes which lead to errors in
            # cryptography (eg. X25519PublicKey.from_public_bytes() in IP Secure handshake)
            # https://github.com/python/cpython/issues/99941
            try:
                if isinstance(asyncio.get_event_loop(), asyncio.ProactorEventLoop):  # type: ignore[attr-defined]
                    self.data_received_callback = lambda data: data_received_callback(
                        bytes(data)
                    )
            except AttributeError:
                # asyncio.ProactorEventLoop is only available on Windows
                pass

        def connection_made(self, transport: asyncio.BaseTransport) -> None:
            """Assign transport. Callback after udp connection was made."""
            self.transport = transport

        def data_received(self, data: bytes) -> None:
            """Call assigned callback. Callback for datagram received."""
            raw_socket_logger.debug("Received via tcp: %s", data.hex())
            self.data_received_callback(data)

        def connection_lost(self, exc: Exception | None) -> None:
            """Log error. Callback for connection lost."""
            logger.debug("Closing TCP transport. %s", exc)
            self.connection_lost_callback()

    def __init__(
        self,
        remote_addr: tuple[str, int],
        connection_lost_cb: Callable[[], None] | None = None,
    ):
        """Initialize TCPTransport class."""
        self.remote_addr = remote_addr
        self.remote_hpai = HPAI(*remote_addr, protocol=HostProtocol.IPV4_TCP)

        self.callbacks = []
        self._connection_lost_cb = connection_lost_cb
        self.transport: asyncio.Transport | None = None
        self._buffer = b""

    def data_received_callback(self, raw: bytes) -> None:
        """Parse and process KNXIP frame. Callback for having received data over TCP."""
        if self._buffer:
            raw = self._buffer + raw
            self._buffer = b""
        if not raw:
            return
        try:
            knxipframe, next_frame_part = KNXIPFrame.from_knx(raw)
        except IncompleteKNXIPFrame:
            self._buffer = raw
            raw_socket_logger.debug(
                "Incomplete KNX/IP frame. Waiting for rest: %s", raw.hex()
            )
            return
        except CouldNotParseKNXIP as couldnotparseknxip:
            knx_logger.debug(
                "Unsupported KNXIPFrame from %s: %s in %s",
                self.remote_hpai,
                couldnotparseknxip.description,
                raw.hex(),
            )
        else:
            knx_logger.debug(
                "Received from %s: %s",
                self.remote_hpai,
                knxipframe,
            )
            self.handle_knxipframe(knxipframe, self.remote_hpai)
        # parse data after current KNX/IP frame
        if next_frame_part:
            self.data_received_callback(next_frame_part)

    async def connect(self) -> None:
        """Connect TCP socket."""
        tcp_transport_factory = TCPTransport.TCPTransportFactory(
            data_received_callback=self.data_received_callback,
            connection_lost_callback=self._connection_lost,
        )
        loop = asyncio.get_running_loop()
        (self.transport, _) = await loop.create_connection(
            lambda: tcp_transport_factory,
            host=self.remote_hpai.ip_addr,
            port=self.remote_hpai.port,
        )

    def _connection_lost(self) -> None:
        """Call assigned callback. Callback for connection lost."""
        # avoid calling the callback when the transport was stopped intentionally
        if self.transport is not None:
            self.stop()
            if self._connection_lost_cb:
                self._connection_lost_cb()

    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame to socket. `addr` is ignored on TCP."""
        knx_logger.debug(
            "Sending to %s: %s",
            self.remote_hpai,
            knxipframe,
        )
        if self.transport is None:
            raise CommunicationError("Transport not connected")

        self.transport.write(knxipframe.to_knx())
