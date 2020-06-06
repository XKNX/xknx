"""
UDPClient is an abstraction for handling the complete UDP io.

The module is built upon anyio udp functions.
Due to nonexisting support of UDP multicast within anyio some special treatment for multicast is necessary.
"""
import anyio
import socket
from sys import platform
from contextlib import contextmanager

from xknx.exceptions import CouldNotParseKNXIP, XKNXException
from xknx.knxip import KNXIPFrame


class UDPClient:
    """Class for handling (sending and receiving) UDP packets."""

    # pylint: disable=too-few-public-methods,too-many-instance-attributes

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
        self.socket = None
        self.callbacks = []
        self._read_task = None

    async def data_received_callback(self, raw, addr):
        """Parse and process KNXIP frame. Callback for having received an UDP packet."""
        if raw:
            self.xknx.raw_socket_logger.debug("Received from %s:%s", addr, raw.hex())
            try:
                knxipframe = KNXIPFrame(self.xknx)
                knxipframe.from_knx(raw)
                self.xknx.knx_logger.debug("Received: %s", knxipframe)
                await self.handle_knxipframe(knxipframe)
            except CouldNotParseKNXIP as couldnotparseknxip:
                self.xknx.logger.exception(couldnotparseknxip)

    async def handle_knxipframe(self, knxipframe):
        """Handle KNXIP Frame and call all callbacks which watch for the service type ident."""
        handled = False
        for callback in self.callbacks:
            if callback.has_service(knxipframe.header.service_type_ident):
                await callback.callback(knxipframe, self)
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

    @contextmanager
    def receiver(self, *service_types):
        """Context manager returning an iterator for incoming packets."""
        q = anyio.create_queue(10)
        async def _receiver(knxipframe, _):
            await q.put(knxipframe)
        try:
            callb = UDPClient.Callback(_receiver, service_types)
            self.callbacks.append(callb)
            yield q
        finally:
            self.callbacks.remove(callb)

    def unregister_callback(self, callb):
        """Unregister callback."""
        self.callbacks.remove(callb)

    @staticmethod
    async def create_multicast_sock(own_ip, remote_addr, bind_to_multicast_addr):
        """Create UDP multicast socket."""
        sock = await anyio.create_udp_socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)

        if own_ip is None:
            # Easy and compatible way to find the IP address of the default interface
            ext_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ext_sock.connect(("8.8.8.8", 53)) # does not send a packet
            own_ip = ext_sock.getsockname()[0]
            ext_sock.close()

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
            socket.SOL_IP,
            socket.IP_MULTICAST_TTL, 2)

        # I have no idea why we have to use different bind calls here
        # - bind() with multicast addr does not work with gateway search requests
        #   on some machines. It only works if called with own ip. It also doesn't
        #   work on Mac OS.
        # - bind() with own_ip does not work with ROUTING_INDICATIONS on Gira
        #   knx router - for an unknown reason.
        if bind_to_multicast_addr:
            if platform == "win32":
                sock.bind(('', remote_addr[1]))
            else:
                sock.bind((remote_addr[0], remote_addr[1]))
        else:
            sock.bind(('0.0.0.0', 0))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        # TODO: filter our own packets instead of turning off loopback
        return sock

    async def connect(self):
        """Connect UDP socket. Open UDP port and build mulitcast socket if necessary."""
        if self.multicast:
            self.socket = await self.create_multicast_sock(self.local_addr[0], self.remote_addr, self.bind_to_multicast_addr)

        else:
            self.socket = await anyio.create_udp_socket(interface=self.local_addr[0], port=self.local_addr[1], target_host=self.remote_addr[0], target_port=self.remote_addr[1])

        self._read_task = await self.xknx.spawn(self._reader)

    async def _reader(self):
        async for raw,addr in self.socket.receive_packets(999):
            await self.data_received_callback(raw, addr)

    async def send(self, knxipframe):
        """Send KNXIPFrame to socket."""
        self.xknx.knx_logger.debug("Sending: %s", knxipframe)
        if self.socket is None:
            raise XKNXException("Transport not connected")

        if self.multicast:
            await self.socket.send(bytes(knxipframe.to_knx()), self.remote_addr)
        else:
            await self.socket.send(bytes(knxipframe.to_knx()))

    def getsockname(self):
        """Return sockname."""
        return self.socket.address

    def getremote(self):
        """Return peername."""
        return self.socket.peer_address

    async def stop(self):
        """Stop UDP socket."""
        if self._read_task is not None:
            await self._read_task.cancel()
        if self.socket is not None:
            await self.socket.close()
