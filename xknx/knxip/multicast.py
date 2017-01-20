import socket
import struct
import threading
from xknx.knx import TelegramDirection
from .knxip import KNXIPFrame
from .knxip_enum import KNXIPServiceType, APCICommand
from .exception import CouldNotParseKNXIP

class Multicast:
    MCAST_GRP = '224.0.23.12'
    MCAST_PORT = 3671

    def __init__(self, xknx):
        self.xknx = xknx


    def send(self, telegram):

        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.ROUTING_INDICATION)
        knxipframe.body.telegram = telegram
        knxipframe.body.sender = self.xknx.globals.own_address
        knxipframe.normalize()

        self._send_knxipframe(knxipframe)


    def _send_knxipframe(self, knxipframe):
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP)
        sock.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL, 2)

        if self.xknx.globals.own_ip is not None:
            sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_IF,
                socket.inet_aton(self.xknx.globals.own_ip))

        knxipframe.normalize()

        sock.sendto(
            bytes(knxipframe.to_knx()),
            (self.MCAST_GRP, self.MCAST_PORT))


    def start_daemon(self):
        print("Starting daemon...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.MCAST_PORT))

        if self.xknx.globals.own_ip is not None:
            sock.setsockopt(socket.IPPROTO_IP,
                            socket.IP_ADD_MEMBERSHIP,
                            socket.inet_aton(self.MCAST_GRP) +
                            socket.inet_aton(self.xknx.globals.own_ip))
        else:
            mreq = struct.pack(
                "4sl",
                socket.inet_aton(self.MCAST_GRP),
                socket.INADDR_ANY)
            sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_ADD_MEMBERSHIP,
                mreq)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        return sock


    def recv(self, sock):
        while True:
            raw = sock.recv(10240)
            if raw:
                try:
                    knxipframe = KNXIPFrame()
                    knxipframe.from_knx(raw)
                    self.handle_frame(knxipframe)
                except CouldNotParseKNXIP as couldnotparseknxip:
                    print(couldnotparseknxip)


    def handle_frame(self, knxipframe):
        if knxipframe.header.service_type_ident == \
                KNXIPServiceType.ROUTING_INDICATION:
            self.handle_frame_routing_indication(knxipframe)
        else:
            print("SERVICE TYPE NOT IMPLEMENETED: ", knxipframe)


    def handle_frame_routing_indication(self, knxipframe):
        if knxipframe.body.src_addr == self.xknx.globals.own_address:
            # Ignoring own KNXIPFrame
            pass
        elif knxipframe.body.cmd not in [APCICommand.GROUP_READ,
                                         APCICommand.GROUP_WRITE,
                                         APCICommand.GROUP_RESPONSE]:
            print("APCI NOT IMPLEMENETED: ", knxipframe)
        else:
            telegram = knxipframe.body.telegram
            telegram.direction = TelegramDirection.INCOMING
            self.xknx.telegrams.put(telegram)


class MulticastDaemon(threading.Thread):
    def __init__(self, xknx):
        self.xknx = xknx
        threading.Thread.__init__(self)


    def run(self):
        multicast = Multicast(self.xknx)
        sock = multicast.start_daemon()
        multicast.recv(sock)


    @staticmethod
    def start_thread(xknx):
        multicastdaemon = MulticastDaemon(xknx)
        multicastdaemon.setDaemon(True)
        multicastdaemon.start()
