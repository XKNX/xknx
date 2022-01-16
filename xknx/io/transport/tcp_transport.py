"""
TCPTransport is an abstraction for handling the complete TCP io.

The module is build upon asyncio stream socket functions.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Callable, cast

from xknx.exceptions import CouldNotParseKNXIP, IncompleteKNXIPFrame, XKNXException
from xknx.knxip import HPAI, HostProtocol, KNXIPFrame

from .ip_transport import KNXIPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

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

        def connection_made(self, transport: asyncio.BaseTransport) -> None:
            """Assign transport. Callback after udp connection was made."""
            self.transport = transport

        def data_received(self, data: bytes) -> None:
            """Call assigned callback. Callback for datagram received."""
            raw_socket_logger.debug("Received via tcp: %s", data.hex())
            self.data_received_callback(data)

        def connection_lost(self, exc: Exception | None) -> None:
            """Log error. Callback for connection lost."""
            logger.debug("Closing transport. %s", exc)
            self.connection_lost_callback()

    def __init__(
        self,
        xknx: XKNX,
        remote_addr: tuple[str, int],
    ):
        """Initialize UDPTransport class."""
        self.xknx = xknx
        self.remote_hpai = HPAI(*remote_addr, protocol=HostProtocol.IPV4_TCP)

        self.callbacks = []
        self.transport: asyncio.Transport | None = None
        self._buffer = bytes()

    def data_received_callback(self, raw: bytes) -> None:
        """Parse and process KNXIP frame. Callback for having received data over TCP."""
        if self._buffer:
            raw = self._buffer + raw
            self._buffer = bytes()
        if not raw:
            return
        try:
            knxipframe = KNXIPFrame(self.xknx)
            frame_length = knxipframe.from_knx(raw)
        except IncompleteKNXIPFrame:
            self._buffer = raw
            raw_socket_logger.debug(
                "Incomplete KNX/IP frame. Waiting for rest: %s", raw.hex()
            )
            return
        except CouldNotParseKNXIP as couldnotparseknxip:
            knx_logger.debug(
                "Unsupported KNXIPFrame from %s at %s: %s in %s",
                self.remote_hpai,
                time.time(),
                couldnotparseknxip.description,
                raw.hex(),
            )
            if not (frame_length := knxipframe.header.total_length):
                return
        else:
            knx_logger.debug(
                "Received from %s at %s:\n%s",
                self.remote_hpai,
                time.time(),
                knxipframe,
            )
            self.handle_knxipframe(knxipframe, self.remote_hpai)
        # parse data after current KNX/IP frame
        if len(raw) > frame_length:
            self.data_received_callback(raw[frame_length:])

    async def connect(self) -> None:
        """Connect TCP socket."""
        tcp_transport_factory = TCPTransport.TCPTransportFactory(
            data_received_callback=self.data_received_callback,
            connection_lost_callback=self.stop,
        )
        loop = asyncio.get_running_loop()
        (transport, _) = await loop.create_connection(
            lambda: tcp_transport_factory,
            host=self.remote_hpai.ip_addr,
            port=self.remote_hpai.port,
        )
        # TODO: typing - remove cast - loop.create_connection should return a asyncio.Transport
        self.transport = cast(asyncio.Transport, transport)

    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame to socket. `addr` is ignored on TCP."""
        knx_logger.debug(
            "Sending to %s at %s:\n%s",
            self.remote_hpai,
            time.time(),
            knxipframe,
        )
        if self.transport is None:
            raise XKNXException("Transport not connected")

        self.transport.write(bytes(knxipframe.to_knx()))
