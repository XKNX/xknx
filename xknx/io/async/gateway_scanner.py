import asyncio
import netifaces
from xknx.knxip import HPAI, KNXIPFrame, SearchResponse, KNXIPServiceType
from .udp_client import UDPClient
from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

class GatewayScanner():

    # pylint: disable=too-many-instance-attributes
    def __init__(self, xknx, timeout_in_seconds=1):
        self.xknx = xknx
        self.response_recieved_or_timeout = asyncio.Event()
        self.found = False
        self.found_ip_addr = None
        self.found_port = None
        self.found_name = None
        self.found_local_ip = None
        self.udpclients = []
        self.timeout_in_seconds = timeout_in_seconds
        self.timeout_callback = None
        self.timeout_handle = None

    def response_rec_callback(self, knxipframe, udp_client):
        if not isinstance(knxipframe.body, SearchResponse):
            print("Cant understand knxipframe")
            return

        if not self.found:
            self.found_ip_addr = knxipframe.body.control_endpoint.ip_addr
            self.found_port = knxipframe.body.control_endpoint.port
            self.found_name = knxipframe.body.device_name

            (self.found_local_ip, _) = udp_client.getsockname()

            self.response_recieved_or_timeout.set()
            self.found = True


    def start(self):
        task = asyncio.Task(self.async_start())
        self.xknx.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_start(self):
        yield from self.send_search_requests()
        yield from self.start_timeout()
        yield from self.response_recieved_or_timeout.wait()
        yield from self.stop()
        yield from self.stop_timeout()

    @asyncio.coroutine
    def stop(self):
        for udpclient in self.udpclients:
            yield from udpclient.stop()


    @asyncio.coroutine
    def send_search_requests(self):
        # pylint: disable=no-member
        for interface in netifaces.interfaces():
            try:
                af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                ip_addr = af_inet[0]["addr"]
                yield from self.search_interface(interface, ip_addr)
            except KeyError:
                #print("NOT CONNECTED", interface)
                continue


    @asyncio.coroutine
    def search_interface(self, interface, ip_addr):
        print("Searching on {0} / {1}".format(interface, ip_addr))

        udpclient = UDPClient(self.xknx,
            (ip_addr, 0),
            (DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT),
            multicast=True)

        udpclient.register_callback(
            self.response_rec_callback, [KNXIPServiceType.SEARCH_RESPONSE])
        yield from udpclient.connect()

        self.udpclients.append(udpclient)

        (local_addr, local_port) = udpclient.getsockname()
        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.SEARCH_REQUEST)
        knxipframe.body.discovery_endpoint = \
            HPAI(ip_addr=local_addr, port=local_port)
        knxipframe.normalize()

        udpclient.send(knxipframe)


    def timeout(self):
        self.response_recieved_or_timeout.set()


    @asyncio.coroutine
    def start_timeout(self):
        self.timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self.timeout)

    @asyncio.coroutine
    def stop_timeout(self):
        self.timeout_handle.cancel()
