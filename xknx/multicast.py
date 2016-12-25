import socket
import struct
import threading 
import time

from .telegram import Telegram
from .address import Address
from .xknx import XKNX
from .devices import CouldNotResolveAddress
from .globals import Globals

class Multicast:
    MCAST_GRP = '224.0.23.12'
    MCAST_PORT = 3671

    def __init__(self, xknx):
        self.xknx = xknx

    def send(self, telegram):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

        if(Globals.get_own_ip()):
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(Globals.get_own_ip()))

        sock.sendto(telegram.str(), (self.MCAST_GRP, self.MCAST_PORT))

    def recv(self, callback = None):
        print("Starting daemon...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("", self.MCAST_PORT))

        if(Globals.get_own_ip()):
            sock.setsockopt(socket.IPPROTO_IP,
                                 socket.IP_ADD_MEMBERSHIP,
                                 socket.inet_aton(self.MCAST_GRP) +
                                 socket.inet_aton(Globals.get_own_ip()))
        else:
            mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

        while True:
            telegram_data = sock.recv(10240)
            if telegram_data:

                if len(telegram_data) < 17:
                    print("WARNING: Telegram has size {0} too small, ignoring".format(len(telegram_data)))
                    continue

                telegram = Telegram()
                telegram.read(telegram_data)

                #telegram.dump()

                if telegram.sender == Globals.get_own_address():
                    #print("Ignoring own telegram")
                    pass

                else:
                    try:
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

