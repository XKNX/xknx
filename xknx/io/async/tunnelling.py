import asyncio
from xknx.knxip import KNXIPServiceType, KNXIPFrame, HPAI, TunnellingAck, ErrorCode
from xknx.knx import Address
from .request_response import RequestResponse

class Tunnelling(RequestResponse):

    def __init__(self, xknx, udp_client, telegram, src_address, sequence_counter, communication_channel):
        self.xknx = xknx
        self.udp_client = udp_client
        self.src_address = src_address

        super(Tunnelling, self).__init__(self.xknx, self.udp_client, TunnellingAck)

        self.telegram = telegram
        self.sequence_counter = sequence_counter
        self.communication_channel = communication_channel


    def create_knxipframe(self):
        (local_addr, local_port) = self.udpclient.getsockname()
        knxipframe = KNXIPFrame()
        knxipframe.init(KNXIPServiceType.TUNNELLING_REQUEST)
        knxipframe.body.communication_channel_id = self.communication_channel
        knxipframe.body.cemi.telegram = self.telegram
        knxipframe.body.cemi.src_addr = self.src_address
        knxipframe.body.sequence_counter = self.sequence_counter
        return knxipframe
