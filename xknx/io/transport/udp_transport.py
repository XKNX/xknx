"""
UDPTransport is an abstraction for handling the complete UDP io.

The module is build upon asyncio udp functions.
Due to lame support of UDP multicast within asyncio some special treatment for multicast is necessary.
"""
from __future__ import annotations

import asyncio
import logging
import socket
from sys import platform
import time
from typing import TYPE_CHECKING, Callable, cast

from xknx.exceptions import CouldNotParseKNXIP, XKNXException
from xknx.knxip import HPAI, KNXIPFrame

from .ip_transport import KNXIPTransport

if TYPE_CHECKING:
    from xknx.xknx import XKNX

raw_socket_logger = logging.getLogger("xknx.raw_socket")
logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")


class UDPTransport(KNXIPTransport):
    """Class for handling (sending and receiving) UDP packets."""

    class UDPTransportFactory(asyncio.DatagramProtocol):
        """Abstraction for managing the asyncio-udp transports."""

        def __init__(
            self,
            own_ip: str,
            multicast: bool = False,
            data_received_callback: Callable[[bytes, tuple[str, int]], None]
            | None = None,
        ):
            """Initialize UDPTransportFactory class."""
            self.own_ip = own_ip
            self.multicast = multicast
            self.transport: asyncio.BaseTransport | None = None
            self.data_received_callback = data_received_callback

        def connection_made(self, transport: asyncio.BaseTransport) -> None:
            """Assign transport. Callback after udp connection was made."""
            self.transport = transport

        def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
            """Call assigned callback. Callback for datagram received."""
            raw_socket_logger.debug("Received from %s: %s", addr, data.hex())
            if self.data_received_callback is not None:
                self.data_received_callback(data, addr)

        def error_received(self, exc: Exception) -> None:
            """Call when a send or receive operation raises an OSError."""
            logger.warning("Error received: %s", exc)

        def connection_lost(self, exc: Exception | None) -> None:
            """Log error. Callback for connection lost."""
            logger.debug("Closing transport.")

    def __init__(
        self,
        xknx: XKNX,
        local_addr: tuple[str, int],
        remote_addr: tuple[str, int],
        multicast: bool = False,
    ):
        """Initialize UDPTransport class."""
        if not isinstance(local_addr, tuple):
            raise TypeError()
        if not isinstance(remote_addr, tuple):
            raise TypeError()
        self.xknx = xknx
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        self.multicast = multicast

        self.callbacks = []
        self.transport: asyncio.DatagramTransport | None = None

    def data_received_callback(self, raw: bytes, source: tuple[str, int]) -> None:
        """Parse and process KNXIP frame. Callback for having received an UDP packet."""
        if raw:
            try:
                knxipframe = KNXIPFrame(self.xknx)
                knxipframe.from_knx(raw)
            except CouldNotParseKNXIP as couldnotparseknxip:
                knx_logger.debug(
                    "Unsupported KNXIPFrame from %s:%s at %s: %s in %s",
                    source[0],
                    source[1],
                    time.time(),
                    couldnotparseknxip.description,
                    raw.hex(),
                )
            else:
                knx_logger.debug(
                    "Received from %s:%s at %s:\n %s",
                    source[0],
                    source[1],
                    time.time(),
                    knxipframe,
                )
                self.handle_knxipframe(knxipframe, HPAI(*source))

    @staticmethod
    def create_multicast_sock(
        own_ip: str, remote_addr: tuple[str, int]
    ) -> socket.socket:
        """Create UDP multicast socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)

        sock.setsockopt(
            socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(own_ip)
        )
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(remote_addr[0]) + socket.inet_aton(own_ip),
        )
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        if platform == "win32":
            # '' represents INADDR_ANY
            sock.bind(("", remote_addr[1]))
        elif platform == "darwin":
            # allows multiple sockets to the same port by multiple processes
            # behaves like SO_REUSEADDR for bind for INADDR_ANY
            # (GatewayScanner opens multiple sockets)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(("", remote_addr[1]))
        else:
            sock.bind((remote_addr[0], remote_addr[1]))

        # ignore multicast datagrams sent by the host itself
        # don't use when running multiple routing instances on a single host (interface)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        return sock

    async def connect(self) -> None:
        """Connect UDP socket. Open UDP port and build mulitcast socket if necessary."""
        udp_transport_factory = UDPTransport.UDPTransportFactory(
            self.local_addr[0],
            multicast=self.multicast,
            data_received_callback=self.data_received_callback,
        )
        loop = asyncio.get_running_loop()
        if self.multicast:
            sock = UDPTransport.create_multicast_sock(
                self.local_addr[0], self.remote_addr
            )
            (transport, _) = await loop.create_datagram_endpoint(
                lambda: udp_transport_factory, sock=sock
            )
            # TODO: typing - remove cast - loop.create_datagram_endpoint should return a DatagramTransport
            self.transport = cast(asyncio.DatagramTransport, transport)

        else:
            (transport, _) = await loop.create_datagram_endpoint(
                lambda: udp_transport_factory,
                local_addr=self.local_addr,
            )
            # TODO: typing - remove cast - loop.create_datagram_endpoint should return a DatagramTransport
            self.transport = cast(asyncio.DatagramTransport, transport)

    def send(self, knxipframe: KNXIPFrame, addr: tuple[str, int] | None = None) -> None:
        """Send KNXIPFrame to socket."""
        _addr = addr or self.remote_addr
        knx_logger.debug(
            "Sending to %s:%s at %s:\n %s", _addr[0], _addr[1], time.time(), knxipframe
        )
        if self.transport is None:
            raise XKNXException("Transport not connected")

        if self.multicast:
            if addr is not None:
                logger.warning(
                    "Multicast send to specific address is invalid. %s",
                    knxipframe,
                )
            self.transport.sendto(bytes(knxipframe.to_knx()), self.remote_addr)
        else:
            self.transport.sendto(bytes(knxipframe.to_knx()), addr=_addr)
