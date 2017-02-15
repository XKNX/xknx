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


    class UDPClientFactory:

        def __init__(self,
                     own_ip,
                     multicast=False,
                     data_received_callback = None):
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


        def datagram_received(self, raw, addr):
            if self.data_received_callback is not None:
                self.data_received_callback(raw)


        def error_received(self, exc):
            # pylint: disable=no-self-use
            print('Error received:', exc)

        def connection_lost(self, exc):
            # pylint: disable=no-self-use
            #print('closing transport', exc)
            pass

    def __init__(self, xknx):
        self.xknx = xknx
        self.transport = None
        self.callbacks = []

    def data_received_callback(self, raw):
        if raw:
            try:
                knxipframe = KNXIPFrame()
                knxipframe.from_knx(raw)
                print("UDP_CLIENT_RECIEVED: ", knxipframe)
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




    @asyncio.coroutine
    def connect(self, own_ip_addr, remote_addr, multicast=False, local_port=0):

        udp_client_factory = UDPClient.UDPClientFactory(
            own_ip_addr, multicast=multicast,
            data_received_callback=self.data_received_callback)

        (transport, _) = yield from self.xknx.loop.create_datagram_endpoint(
            lambda: udp_client_factory,
            local_addr=(own_ip_addr, local_port),
            remote_addr=remote_addr)

        self.transport = transport


    def send(self, knxipframe):
        if self.transport is None:
            raise Exception("Transport not connected")
        self.transport.sendto(bytes(knxipframe.to_knx()))


    @asyncio.coroutine
    def stop(self):
        yield from asyncio.sleep(1/20)
        self.transport.close()
