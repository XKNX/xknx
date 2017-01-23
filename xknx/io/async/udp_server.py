import asyncio
import socket
import struct
from xknx.knxip import KNXIPFrame, CouldNotParseKNXIP, KNXIPServiceType
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

class UDPServer:

    class Callback:
        def __init__(self, callback, service_types=[]):
            self.callback = callback
            self.service_types = service_types

        def has_service(self, service_type):
            return \
                len(self.service_types) == 0 or \
                service_type in self.service_types


    class UDPServerFactory:

        def __init__(self,
                     multicast_group=None,
                     data_received_callback=None):
            self.multicast_group = multicast_group
            self.data_received_callback = data_received_callback


        def connection_made(self, transport):
            self.transport = transport

            if self.multicast_group is not None:
                self.init_multicast(self.multicast_group)


        def init_multicast(self, multicast_group):
            sock = self.transport.get_extra_info('socket')
            group = socket.inet_aton(multicast_group)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


        def datagram_received(self, raw, addr):
            if self.data_received_callback is not None:
                self.data_received_callback(raw)


        def error_received(self, exc):
            print('Error received:', exc)

        def connection_lost(self, exc):
            print('stop', exc)


    def __init__(self, xknx, loop):
        self.xknx = xknx
        self.loop = loop
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


    def register_callback(self, callback, service_types=[]):
        self.callbacks.append(UDPServer.Callback(callback, service_types))


    @asyncio.coroutine
    def start(self):

        addr = (DEFAULT_MCAST_GRP,DEFAULT_MCAST_PORT)

        udp_server_factory = UDPServer.UDPServerFactory(
            multicast_group=DEFAULT_MCAST_GRP,
            data_received_callback=self.data_received_callback)

        # Add reuse_address at a later stage. Looks like these
        # parameters are not yet supported by python 3.5
        # , reuse_address=True, reuse_port=True)) 
        (transport, _) = yield from self.loop.create_datagram_endpoint(
            lambda: udp_server_factory, local_addr=addr)
        self.transport = transport


    def stop(self):
        self.transport.close()
