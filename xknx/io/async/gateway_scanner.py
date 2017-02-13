import asyncio
import netifaces
from xknx.knxip import HPAI, KNXIPFrame, SearchResponse, KNXIPServiceType
from .udp_server import UDPServer
from .udp_client import UDPClient
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

class GatewayScanner():

    def __init__(self, xknx):
        self.xknx = xknx
        self.search_response_recieved = asyncio.Event()
        self.found = False
        self.found_ip_addr = None
        self.found_port = None
        self.found_name = None
        self.udpservers = []

    def response_rec_callback(self, knxipframe):
        if not isinstance(knxipframe.body, SearchResponse):
            print("Cant understand knxipframe")
            return

        if not self.found:
            self.found_ip_addr = knxipframe.body.control_endpoint.ip_addr
            self.found_port = knxipframe.body.control_endpoint.port
            self.found_name = knxipframe.body.device_name
            self.search_response_recieved.set()
            self.found = True


    def start(self):
        task = asyncio.Task(self.async_start())
        self.xknx.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_start(self):
        yield from self.send_search_requests()
        yield from self.search_response_recieved.wait()
        yield from self.stop()


    @asyncio.coroutine
    def stop(self):
        for udpserver in self.udpservers:
            udpserver.stop()


    @asyncio.coroutine
    def send_search_requests(self):
        # pylint: disable=no-member
        for interface in netifaces.interfaces():
            af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
            ip_addr = af_inet[0]["addr"]
            yield from self.search_interface(interface, ip_addr)


    @asyncio.coroutine
    def search_interface(self, interface, ip_addr):
        print("Searching on {0} / {1}".format(interface, ip_addr))

        udpserver = UDPServer(self.xknx, own_ip=ip_addr)
        udpserver.register_callback(
            self.response_rec_callback, [KNXIPServiceType.SEARCH_RESPONSE])

        yield from udpserver.start()

        self.udpservers.append(udpserver)

        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe.body.discovery_endpoint = \
            HPAI(ip_addr=DEFAULT_MCAST_GRP, port=DEFAULT_MCAST_PORT)
        knxipframe.normalize()

        udpclient = UDPClient(self.xknx)
        yield from udpclient.connect(
            ip_addr,
            (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            multicast=True)
        udpclient.send(knxipframe)
