import asyncio
from xknx.knxip import KNXIPServiceType, KNXIPFrame, ConnectRequestType, HPAI, ConnectResponse, ErrorCode
from .request_response import RequestResponse

class Connect(RequestResponse):

    def __init__(self, xknx, udp_client):
        self.xknx = xknx
        self.udp_client = udp_client
        super(Connect, self).__init__(self.xknx, self.udp_client, ConnectResponse)
        self.communication_channel = 0
        self.identifier = 0


    def create_knxipframe(self):
        (local_addr, local_port) = self.udp_client.getsockname()
        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.CONNECT_REQUEST)
        knxipframe.body.request_type = ConnectRequestType.TUNNEL_CONNECTION

        # set control_endpoint and data_endpoint to the same udp_connection
        knxipframe.body.control_endpoint = HPAI(
            ip_addr=local_addr, port=local_port)
        knxipframe.body.data_endpoint = HPAI(
            ip_addr=local_addr, port=local_port)
        return knxipframe


    def on_success_hook(self, knxipframe):
        self.communication_channel = knxipframe.body.communication_channel
        self.identifier = knxipframe.body.identifier

