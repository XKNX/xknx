"""
UDPClient is an abstraction for handling the complete UDP io.

The module is build upon asyncio udp functions.
Due to lame support of UDP multicast within asyncio some special treatment for multicast is necessary.
"""
import asyncio
import socket

from xknx.exceptions import CouldNotParseKNXIP, XKNXException
from xknx.knxip import KNXIPFrame


class UDPClient:
    """Class for handling (sending and receiving) UDP packets."""

    # pylint: disable=too-few-public-methods

    class Callback:
        """Callback class for handling callbacks for different 'KNX service types' of received packets."""

        def __init__(self, callback, service_types=None):
            """Initialize Callback class."""
            self.callback = callback
            self.service_types = service_types or []

        def has_service(self, service_type):
            """Test if callback is listening for given service type."""
            return \
                len(self.service_types) == 0 or \
                service_type in self.service_types

    class UDPClientFactory(asyncio.DatagramProtocol):
        """Abstraction for managing the asyncio-udp transports."""

        def __init__(self,
                     xknx,
                     own_ip,
                     multicast=False,
                     data_received_callback=None):
            """Initialize UDPClientFactory class."""
            self.xknx = xknx
            self.own_ip = own_ip
            self.multicast = multicast
            self.transport = None
            self.data_received_callback = data_received_callback

        def connection_made(self, transport):
            """Assign transport. Callback after udp connection was made."""
            self.transport = transport

        def datagram_received(self, data, addr):
            """Call assigned callback. Callback for datagram received."""
            if self.data_received_callback is not None:
                self.data_received_callback(data)

        def error_received(self, exc):
            """Handel errors. Callback for error received."""
            self.xknx.logger.warning('Error received: %s', exc)

        def connection_lost(self, exc):
            """Log error. Callback for connection lost."""
            self.xknx.logger.info('closing transport %s', exc)

    def __init__(self, xknx, local_addr, remote_addr, multicast=False, bind_to_multicast_addr=False):
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
        self.bind_to_multicast_addr = bind_to_multicast_addr
        self.transport = None
        self.callbacks = []

    def data_received_callback(self, raw):
        """Parse and process KNXIP frame. Callback for having received an UDP packet."""
        if raw:
            try:
                knxipframe = KNXIPFrame(self.xknx)
                knxipframe.from_knx(raw)
                self.xknx.knx_logger.debug("Received: %s", knxipframe)
                self.handle_knxipframe(knxipframe)
            except CouldNotParseKNXIP as couldnotparseknxip:
                self.xknx.logger.exception(couldnotparseknxip)

    def handle_knxipframe(self, knxipframe):
        """Handle KNXIP Frame and call all callbacks which watch for the service type ident."""
        handled = False
        for callback in self.callbacks:
            if callback.has_service(knxipframe.header.service_type_ident):
                callback.callback(knxipframe, self)
                handled = True
        if not handled:
            self.xknx.logger.debug("UNHANDLED: %s", knxipframe.header.service_type_ident)

    def register_callback(self, callback, service_types=None):
        """Register callback."""
        if service_types is None:
            service_types = []

        callb = UDPClient.Callback(callback, service_types)
        self.callbacks.append(callb)
        return callb

    def unregister_callback(self, callb):
        """Unregister callback."""
        self.callbacks.remove(callb)

    @staticmethod
    def create_multicast_sock(own_ip, remote_addr, bind_to_multicast_addr):
        """Create UDP multicast socket."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)

        sock.setsockopt(
            socket.SOL_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(own_ip))
        sock.setsockopt(
            socket.SOL_IP,
            socket.IP_ADD_MEMBERSHIP,
            socket.inet_aton(remote_addr[0]) +
            socket.inet_aton(own_ip))
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL, 2)
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_IF,
            socket.inet_aton(own_ip))

        # I have no idea why we have to use different bind calls here
        # - bind() with multicast addr does not work with gateway search requests
        #   on some machines. It only works if called with own ip.
        # - bind() with own_ip does not work with ROUTING_INDICATIONS on Gira
        #   knx router - for an unknown reason.
        if bind_to_multicast_addr:
            sock.bind((remote_addr[0], remote_addr[1]))
        else:
            sock.bind((own_ip, 0))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        return sock

    async def connect(self):
        """Connect UDP socket. Open UDP port and build mulitcast socket if necessary."""
        udp_client_factory = UDPClient.UDPClientFactory(
            self.xknx, self.local_addr[0], multicast=self.multicast,
            data_received_callback=self.data_received_callback)

        if self.multicast:
            sock = UDPClient.create_multicast_sock(self.local_addr[0], self.remote_addr, self.bind_to_multicast_addr)
            (transport, _) = await self.xknx.loop.create_datagram_endpoint(
                lambda: udp_client_factory, sock=sock)
            self.transport = transport

        else:
            (transport, _) = await self.xknx.loop.create_datagram_endpoint(
                lambda: udp_client_factory,
                local_addr=self.local_addr,
                remote_addr=self.remote_addr)
            self.transport = transport

    def send(self, knxipframe):
        """Send KNXIPFrame to socket."""
        self.xknx.knx_logger.debug("Sending: %s", knxipframe)
        if self.transport is None:
            raise XKNXException("Transport not connected")

        if self.multicast:
            self.transport.sendto(bytes(knxipframe.to_knx()), self.remote_addr)
        else:
            self.transport.sendto(bytes(knxipframe.to_knx()))

    def getsockname(self):
        """Return sockname."""
        sock = self.transport.get_extra_info("sockname")
        return sock

    def getremote(self):
        """Return peername."""
        peer = self.transport.get_extra_info('peername')
        return peer

    async def stop(self):
        """Stop UDP socket."""
        self.transport.close()
