import socket
import struct
import threading
import time

from .telegram import Telegram,TelegramDirection
from .knxip import KNXIPFrame
from .address import Address
from .xknx import XKNX
from .devices import CouldNotResolveAddress

class Multicast:
    MCAST_GRP = '224.0.23.12'
    MCAST_PORT = 3671

    def __init__(self, xknx):
        self.xknx = xknx

    def send(self, telegram):

        knxipframe = KNXIPFrame()
        knxipframe.telegram = telegram
        knxipframe.sender = self.xknx.globals.own_address
        knxipframe.normalize()

        self._send_knxipframe(knxipframe)

    def _send_knxipframe( self, knxipframe):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        if self.xknx.globals.own_ip is not None:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.xknx.globals.own_ip))

        knxipframe.normalize()
        sock.sendto(bytes(knxipframe.to_knx()), (self.MCAST_GRP, self.MCAST_PORT))

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
            mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        return sock

    def recv(self,sock):
        while True:
            raw = sock.recv(10240)
            if raw:

                if len(raw) < 17:
                    print("WARNING: KNXIPFrame has size {0} too small, ignoring".format(len(raw)))
                    continue

                knxipframe = KNXIPFrame()
                knxipframe.from_knx(raw)

                if knxipframe.sender == self.xknx.globals.own_address:
                    # Ignoring own KNXIPFrame
                    pass

                else:
                    telegram = knxipframe.telegram
                    # TODO: This should be inside knxipframe
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
        t = MulticastDaemon(xknx)
        t.setDaemon(True)
        t.start()

