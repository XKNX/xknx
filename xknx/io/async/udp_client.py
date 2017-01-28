import asyncio
import socket

class UDPClient:

    class UDPClientFactory:

        def __init__(self,
                     knxipframe,
                     own_ip,
                     multicast=False):
            self.knxipframe = knxipframe
            self.own_ip = own_ip
            self.multicast = multicast

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

            self.transport.sendto(bytes(self.knxipframe.to_knx()))

        def datagram_received(self, data, addr):
            print('received "{}"'.format(data.decode()))
            self.transport.close()

        def error_received(self, exc):
            print('Error received:', exc)

        def connection_lost(self, exc):
            print('closing transport', exc)
            loop = asyncio.get_event_loop()
            loop.stop()

    def __init__(self, xknx, loop):
        self.xknx = xknx
        self.loop = loop
        self.transport = None

    @asyncio.coroutine
    def send(self, own_ip_addr, remote_addr, knxipframe, multicast=False):

        udp_client_factory = UDPClient.UDPClientFactory(
            knxipframe, own_ip_addr, multicast=multicast)

        yield from self.loop.create_datagram_endpoint(
            lambda: udp_client_factory, local_addr=(own_ip_addr, 3671), remote_addr=remote_addr)

