import asyncio
from xknx.knxip import KNXIPServiceType, KNXIPFrame, ConnectRequestType, HPAI, ConnectResponse, ErrorCode
from .udp_client import UDPClient


class KNXIPTunnel():

    def __init__(self, xknx, own_ip, gateway_ip, gateway_port, timeout_in_seconds=1):
        self.xknx = xknx
        self.own_ip = own_ip
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port

        self.response_recieved_or_timeout = asyncio.Event()

        self.success = False
        self.communication_channel = 0
        self.identifier = 0

        self.udpclient = UDPClient(self.xknx)
        self.udpclient.register_callback(
            self.response_rec_callback, [KNXIPServiceType.CONNECT_RESPONSE])

        self.timeout_in_seconds = timeout_in_seconds
        self.timeout_callback = None
        self.timeout_handle = None

    def start(self):
        task = asyncio.Task(self.async_start())
        self.xknx.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_start(self):
        print("Starting tunnel at {0}:{1}".format(self.gateway_ip, self.gateway_port))

        yield from self.send_connect_request()
        yield from self.start_timeout()
        yield from self.response_recieved_or_timeout.wait()
        yield from self.stop()
        yield from self.stop_timeout()



    @asyncio.coroutine
    def send_connect_request(self):

        yield from self.udpclient.connect(
            self.own_ip,
            (self.gateway_ip, self.gateway_port),
            multicast=False)
    
        (local_addr, local_port) = self.udpclient.getsockname()

        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.CONNECT_REQUEST)
        knxipframe.body.request_type = ConnectRequestType.TUNNEL_CONNECTION
        knxipframe.body.control_endpoint = HPAI(
            ip_addr=local_addr, port=local_port)
        knxipframe.body.data_endpoint = HPAI(
            ip_addr=self.gateway_ip, port=self.gateway_port)
        knxipframe.normalize()
        self.udpclient.send(knxipframe)



    def response_rec_callback(self, knxipframe):
        if not isinstance(knxipframe.body, ConnectResponse):
            print("Cant understand knxipframe")
            return

        self.response_recieved_or_timeout.set()

        if knxipframe.body.status_code == ErrorCode.E_NO_ERROR:
            self.success = True
            self.communication_channel = knxipframe.body.communication_channel
            self.identifier = knxipframe.body.identifier
        else:
            print("Error Connect failed: ", knxipframe.body.status_code)


    @asyncio.coroutine
    def stop(self):
        self.udpclient.stop()


    def timeout(self):
        self.response_recieved_or_timeout.set()


    @asyncio.coroutine
    def start_timeout(self):
        self.timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self.timeout)


    @asyncio.coroutine
    def stop_timeout(self):
        self.timeout_handle.cancel()
