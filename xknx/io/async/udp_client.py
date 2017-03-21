import asyncio
import socket

from xknx.knxip import KNXIPFrame, CouldNotParseKNXIP


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

    def __init__(self, xknx, local_addr, remote_addr, multicast=False, bind_to_multicast_addr=False):
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


    def create_multicast_sock(self, own_ip, remote_addr, bind_to_multicast_addr):
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

    @asyncio.coroutine
    def connect(self):

        udp_client_factory = UDPClient.UDPClientFactory(
            self.local_addr[0], multicast=self.multicast,
            data_received_callback=self.data_received_callback)

        if self.multicast:
            sock = self.create_multicast_sock(self.local_addr[0], self.remote_addr, self.bind_to_multicast_addr)
            (transport, _) = yield from self.xknx.loop.create_datagram_endpoint(
                lambda: udp_client_factory, sock=sock)
            self.transport = transport

        else:
            (transport, _) = yield from self.xknx.loop.create_datagram_endpoint(
                lambda: udp_client_factory,
                local_addr=self.local_addr,
                remote_addr=self.remote_addr)
            self.transport = transport


    def send(self, knxipframe):
        if self.transport is None:
            raise Exception("Transport not connected")

        if self.multicast:
            self.transport.sendto(bytes(knxipframe.to_knx()), self.remote_addr)
        else:
            self.transport.sendto(bytes(knxipframe.to_knx()))


    def getsockname(self):
        sock = self.transport.get_extra_info("sockname")
        return sock

    def getremote(self):
        peer = self.transport.get_extra_info('peername')
        return peer

    @asyncio.coroutine
    def stop(self):
        #yield from asyncio.sleep(1/20)
        self.transport.close()
