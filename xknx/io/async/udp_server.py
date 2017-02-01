import asyncio
import socket
from xknx.knxip import KNXIPFrame, CouldNotParseKNXIP
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

class UDPServer:
    # pylint: disable=too-few-public-methods

    class Callback:
        def __init__(self, callback, service_types=None):
            self.callback = callback
            self.service_types = service_types or []

        def has_service(self, service_type):
            return \
                len(self.service_types) == 0 or \
                service_type in self.service_types


    class UDPServerFactory(asyncio.DatagramProtocol):

        def __init__(self, data_received_callback=None):
            self.data_received_callback = data_received_callback
            self.transport = None


        def connection_made(self, transport):
            self.transport = transport


        def datagram_received(self, raw, addr):
            if self.data_received_callback is not None:
                self.data_received_callback(raw)


        def error_received(self, exc):
            print('Error received:', exc)


        def connection_lost(self, exc):
            print('stop', exc)


    def __init__(self, xknx, multicast=False, own_ip=None):
        self.xknx = xknx
        self.multicast = multicast
        self.own_ip = own_ip
        self.loop = xknx.loop
        self.transport = None
        self.callbacks = []


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
                callback.callback(knxipframe)
                handled = True
        if not handled:
            #print("UNHANDLED: ", knxipframe.header.service_type_ident)
            pass


    def register_callback(self, callback, service_types=None):
        if service_types is None:
            service_types = []
        self.callbacks.append(UDPServer.Callback(callback, service_types))


    def create_sock(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(False)

        if self.own_ip is not None:
            sock.setsockopt(
                socket.SOL_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(self.own_ip))
            sock.setsockopt(
                socket.SOL_IP,
                socket.IP_ADD_MEMBERSHIP,
                socket.inet_aton(DEFAULT_MCAST_GRP) +
                socket.inet_aton(self.own_ip))

        sock.bind(("", DEFAULT_MCAST_PORT))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        return sock


    @asyncio.coroutine
    def start(self):

        udp_server_factory = UDPServer.UDPServerFactory(
            data_received_callback=self.data_received_callback)

        sock = self.create_sock()

        (transport, _) = yield from self.loop.create_datagram_endpoint(
            lambda: udp_server_factory, sock=sock)

        self.transport = transport


    def stop(self):
        self.transport.close()
