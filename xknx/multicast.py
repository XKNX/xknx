import socket
import struct
import threading
import time

from .telegram import Telegram
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

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        if self.xknx.globals.own_ip is not None:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(self.xknx.globals.own_ip))

        sock.sendto(knxipframe.str(), (self.MCAST_GRP, self.MCAST_PORT))

    def recv(self, callback = None):
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

        while True:
            raw = sock.recv(10240)
            if raw:

                if len(raw) < 17:
                    print("WARNING: KNXIPFrame has size {0} too small, ignoring".format(len(raw)))
                    continue

                knxipframe = KNXIPFrame()
                knxipframe.read(raw)

                #knxipframe.dump()

                if knxipframe.sender == self.xknx.globals.own_address:
                    #print("Ignoring own KNXIPFrame")
                    pass

                else:
                    try:

                        telegram = knxipframe.telegram
                        device = self.xknx.devices.device_by_group_address(telegram.group_address)
                        device.process(telegram)

                        if ( callback ):
                            callback(self.xknx, device,telegram)

                    except CouldNotResolveAddress as c:
                        print(c)



class MulticastSender(threading.Thread):
    def __init__(self, xknx):
        self.xknx = xknx
        threading.Thread.__init__(self)

    def run(self):
        while True:
            telegram = self.xknx.out_queue.get()
            self.process_telegram(telegram)
            self.xknx.out_queue.task_done()
            # limit rate to knx bus to 20 per second
            time.sleep(1/20)

    def process_telegram(self,telegram):
        multicast = Multicast(self.xknx)
        multicast.send(telegram)

    @staticmethod
    def start_thread(xknx):
        t = MulticastSender(xknx)
        t.setDaemon(True)
        t.start()

class MulticastReceiver(threading.Thread):
    def __init__(self, xknx, callback = None):
        self.xknx = xknx
        self.callback = callback
        threading.Thread.__init__(self)

    def run(self):
        Multicast(self.xknx).recv(self.callback)

    @staticmethod
    def start_thread(xknx, callback = None):
        t = MulticastReceiver(xknx, callback)
        t.setDaemon(True)
        t.start()

