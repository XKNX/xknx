"""
UDPClient is an abstraction for handling the complete UDP io.

The module is build upon asyncio udp functions.
Due to lame support of UDP multicast within asyncio some special treatment for multicast is necessary.
"""
import asyncio
import logging
import socket
from sys import platform
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple, cast

from xknx.exceptions import CommunicationError, CouldNotParseKNXIP, XKNXException
from xknx.knxip import KNXIPFrame, KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX

    CallbackType = Callable[[KNXIPFrame, "UDPClient"], None]

raw_socket_logger = logging.getLogger("xknx.raw_socket")
logger = logging.getLogger("xknx.log")
knx_logger = logging.getLogger("xknx.knx")


class UDPClient:
    """Class for handling (sending and receiving) UDP packets."""

    # pylint: disable=too-few-public-methods

    class Callback:
        """Callback class for handling callbacks for different 'KNX service types' of received packets."""

        def __init__(
            self,
            callback: "CallbackType",
            service_types: Optional[List[KNXIPServiceType]] = None,
        ):
            """Initialize Callback class."""
            self.callback = callback
            self.service_types = service_types or []

        def has_service(self, service_type: KNXIPServiceType) -> bool:
            """Test if callback is listening for given service type."""
            return len(self.service_types) == 0 or service_type in self.service_types

    class UDPClientFactory(asyncio.DatagramProtocol):
        """Abstraction for managing the asyncio-udp transports."""

        def __init__(
            self,
            own_ip: str,
            multicast: bool = False,
            data_received_callback: Optional[Callable[[bytes], None]] = None,
        ):
            """Initialize UDPClientFactory class."""
            self.own_ip = own_ip
            self.multicast = multicast
            self.transport: Optional[asyncio.BaseTransport] = None
            self.data_received_callback = data_received_callback

        def connection_made(self, transport: asyncio.BaseTransport) -> None:
            """Assign transport. Callback after udp connection was made."""
            self.transport = transport

        def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
            """Call assigned callback. Callback for datagram received."""
            raw_socket_logger.debug("Received from %s: %s", addr, data.hex())
            if self.data_received_callback is not None:
                self.data_received_callback(data)

        def error_received(self, exc: Exception) -> None:
            """Call when a send or receive operation raises an OSError."""
            logger.warning("Error received: %s", exc)

        def connection_lost(self, exc: Optional[Exception]) -> None:
            """Log error. Callback for connection lost."""
            logger.debug("Closing transport.")

    def __init__(
        self,
        xknx: "XKNX",
        local_addr: Tuple[str, int],
        remote_addr: Tuple[str, int],
        multicast: bool = False,
    ):
        """Initialize UDPClient class."""
        # pylint: disable=too-many-arguments
        if not isinstance(local_addr, tuple):
            raise TypeError()
        if not isinstance(remote_addr, tuple):
            raise TypeError()
        self.xknx = xknx
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        self.multicast = multicast
        self.callbacks: List["UDPClient.Callback"] = []

        self.transport: Optional[asyncio.DatagramTransport] = None

    def data_received_callback(self, raw: bytes) -> None:
        """Parse and process KNXIP frame. Callback for having received an UDP packet."""
        if raw:
            try:
                knxipframe = KNXIPFrame(self.xknx)
                knxipframe.from_knx(raw)
            except CouldNotParseKNXIP as couldnotparseknxip:
                knx_logger.debug(
                    "Unsupported KNXIPFrame: %s in %s",
                    couldnotparseknxip.description,
                    raw.hex(),
                )
            else:
                knx_logger.debug("Received: %s", knxipframe)
                self.handle_knxipframe(knxipframe)

    def handle_knxipframe(self, knxipframe: KNXIPFrame) -> None:
        """Handle KNXIP Frame and call all callbacks which watch for the service type ident."""
        handled = False
        for callback in self.callbacks:
            if callback.has_service(knxipframe.header.service_type_ident):
                callback.callback(knxipframe, self)
                handled = True
        if not handled:
            knx_logger.debug(
                "Unhandled %s: %s", knxipframe.header.service_type_ident, knxipframe
            )

    def register_callback(
        self,
        callback: "CallbackType",
        service_types: Optional[List[KNXIPServiceType]] = None,
    ) -> "UDPClient.Callback":
        """Register callback."""
        if service_types is None:
            service_types = []

        callb = UDPClient.Callback(callback, service_types)
        self.callbacks.append(callb)
        return callb

    def unregister_callback(self, callb: "UDPClient.Callback") -> None:
        """Unregister callback."""
        self.callbacks.remove(callb)

    @staticmethod
    def create_multicast_sock(
        own_ip: str, remote_addr: Tuple[str, int]
    ) -> socket.SocketType:
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
        udp_client_factory = UDPClient.UDPClientFactory(
            self.local_addr[0],
            multicast=self.multicast,
            data_received_callback=self.data_received_callback,
        )
        loop = asyncio.get_running_loop()
        if self.multicast:
            sock = UDPClient.create_multicast_sock(self.local_addr[0], self.remote_addr)
            (transport, _) = await loop.create_datagram_endpoint(
                lambda: udp_client_factory, sock=sock
            )
            # TODO: typing - remove cast - loop.create_datagram_endpoint should return a DatagramTransport
            self.transport = cast(asyncio.DatagramTransport, transport)

        else:
            (transport, _) = await loop.create_datagram_endpoint(
                lambda: udp_client_factory,
                local_addr=self.local_addr,
                remote_addr=self.remote_addr,
            )
            # TODO: typing - remove cast - loop.create_datagram_endpoint should return a DatagramTransport
            self.transport = cast(asyncio.DatagramTransport, transport)

    def send(self, knxipframe: KNXIPFrame) -> None:
        """Send KNXIPFrame to socket."""
        knx_logger.debug("Sending: %s", knxipframe)
        if self.transport is None:
            raise XKNXException("Transport not connected")

        if self.multicast:
            self.transport.sendto(bytes(knxipframe.to_knx()), self.remote_addr)
        else:
            self.transport.sendto(bytes(knxipframe.to_knx()))

    def getsockname(self) -> Tuple[str, int]:
        """Return socket IP and port."""
        if self.transport is None:
            raise CommunicationError(
                "No transport defined. Socket information not resolveable"
            )
        return cast(Tuple[str, int], self.transport.get_extra_info("sockname"))

    def getremote(self) -> Optional[str]:
        """Return peername."""
        return (
            self.transport.get_extra_info("peername")
            if self.transport is not None
            else None
        )

    async def stop(self) -> None:
        """Stop UDP socket."""
        if self.transport is not None:
            self.transport.close()
