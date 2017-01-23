import asyncio
import netifaces
from xknx.knxip import HPAI, KNXIPFrame, SearchResponse, KNXIPServiceType
from .udp_server import UDPServer
from .udp_client import UDPClient
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

class GatewayScanner():

    def __init__(self, xknx, loop):
        self.xknx = xknx
        self.loop = loop
        self.search_response_recieved = asyncio.Event()
        self.found = False
        self.found_ip_addr = None
        self.found_port = None

    def response_rec_callback(self, knxipframe):
        if not isinstance(knxipframe.body, SearchResponse):
            print("Cant understand knxipframe")
            return

        print("FOUND: {0}:{1} ({2})".format(
            knxipframe.body.control_endpoint.ip_addr,
            knxipframe.body.control_endpoint.port,
            knxipframe.body.device_name))

        if not self.found:
            self.found_ip_addr=knxipframe.body.control_endpoint.ip_addr
            self.found_port=knxipframe.body.control_endpoint.port
            self.search_response_recieved.set()
            self.found = True

    @asyncio.coroutine
    def start_scan(self):
        udpserver = UDPServer(self.xknx, self.loop)
        udpserver.register_callback(
            self.response_rec_callback, [KNXIPServiceType.SEARCH_RESPONSE])

        yield from udpserver.start()
        yield from self.send_search_requests()
        yield from self.search_response_recieved.wait()


    @asyncio.coroutine
    def send_search_requests(self):
        for interface in netifaces.interfaces():
            af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
            ip_addr = af_inet[0]["addr"]
            yield from self.search_interface(interface, ip_addr)


    @asyncio.coroutine
    def search_interface(self, interface, ip_addr):
        print("Searching on {0} / {1}".format(interface, ip_addr))

        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe.body.discovery_endpoint = \
            HPAI(ip_addr=DEFAULT_MCAST_GRP, port=DEFAULT_MCAST_PORT)
        knxipframe.normalize()

        udpclient = UDPClient(self.xknx, self.loop)
        yield from udpclient.send(
            ip_addr,
            (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            knxipframe,
            multicast=True)
