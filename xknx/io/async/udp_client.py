import asyncio
import socket

from xknx.knxip import KNXIPFrame, CouldNotParseKNXIP
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

class UDPClient:

    class Callback:
        def __init__(self, callback, service_types=None):
            self.callback = callback
            self.service_types = service_types or []

        def has_service(self, service_type):
            return \
                len(self.service_types) == 0 or \
                service_type in self.service_types


    class UDPClientFactory(asyncio.DatagramProtocol):

        def __init__(self,
                     own_ip,
                     multicast=False,
                     data_received_callback=None):
            self.own_ip = own_ip
            self.multicast = multicast
            self.transport = None
            self.data_received_callback = data_received_callback

        def connection_made(self, transport):
            self.transport = transport

            sock = self.transport.get_extra_info('socket')
            sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_TTL, 2)

            if self.multicast:
                sock.setsockopt(
                    socket.IPPROTO_IP,
                    socket.IP_MULTICAST_IF,
                    socket.inet_aton(self.own_ip))


        def datagram_received(self, raw, _):
            if self.data_received_callback is not None:
                self.data_received_callback(raw)


        def error_received(self, exc):
            # pylint: disable=no-self-use
            print('Error received:', exc)

        def connection_lost(self, exc):
            # pylint: disable=no-self-use
            #print('closing transport', exc)
            pass

    def __init__(self, xknx, multicast=False):
        self.xknx = xknx
        self.transport = None
        self.callbacks = []
        self.multicast = multicast

    def data_received_callback(self, raw):
        if raw:
            try:
                knxipframe = KNXIPFrame()
                knxipframe.from_knx(raw)
                self.handle_knxipframe(knxipframe)
            except CouldNotParseKNXIP as couldnotparseknxip:
                print(couldnotparseknxip)


    def handle_knxipframe(self, knxipframe):
        handled = False
        for callback in self.callbacks:
            if callback.has_service(knxipframe.header.service_type_ident):
                callback.callback(knxipframe, self)
                handled = True
        if not handled:
            #print("UNHANDLED: ", knxipframe.header.service_type_ident)
            pass


    def register_callback(self, callback, service_types=None):
        if service_types is None:
            service_types = []

        cb = UDPClient.Callback(callback, service_types)
        self.callbacks.append(cb)
        return cb


    def unregister_callback(self, cb):
        self.callbacks.remove(cb)


    def create_multicast_sock(self, own_ip):
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
                socket.inet_aton(DEFAULT_MCAST_GRP) +
                socket.inet_aton(own_ip))
        sock.bind(("", DEFAULT_MCAST_PORT))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        return sock

    @asyncio.coroutine
    def connect(self, own_ip_addr, remote_addr, local_port=0):

        udp_client_factory = UDPClient.UDPClientFactory(
            own_ip_addr, multicast=self.multicast,
            data_received_callback=self.data_received_callback)

        if self.multicast:
            sock = self.create_multicast_sock(own_ip_addr)
            (transport, _) = yield from self.xknx.loop.create_datagram_endpoint(
                lambda: udp_client_factory, sock=sock)
            self.transport = transport

        else:
            (transport, _) = yield from self.xknx.loop.create_datagram_endpoint(
                lambda: udp_client_factory,
                local_addr=(own_ip_addr, local_port),
                remote_addr=remote_addr)
            self.transport = transport


    def send(self, knxipframe):
        if self.transport is None:
            raise Exception("Transport not connected")

        if self.multicast:
            self.transport.sendto(bytes(knxipframe.to_knx()), (DEFAULT_MCAST_GRP,DEFAULT_MCAST_PORT) )
        else:
            self.transport.sendto(bytes(knxipframe.to_knx()))


    def getsockname(self):
        sock = self.transport.get_extra_info("socket")
        return sock.getsockname()

    def getremote(self):
        peer = self.transport.get_extra_info('peername')
        return peer

    @asyncio.coroutine
    def stop(self):
        yield from asyncio.sleep(1/20)
        self.transport.close()
