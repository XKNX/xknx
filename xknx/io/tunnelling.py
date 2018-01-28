"""Abstraction to send a TunnelingRequest and wait for TunnelingResponse."""
from xknx.knxip import KNXIPFrame, KNXIPServiceType, TunnellingAck

from .request_response import RequestResponse


class Tunnelling(RequestResponse):
    """Class to TunnelingRequest and wait for TunnelingResponse."""

    def __init__(self, xknx, udp_client, telegram, src_address, sequence_counter, communication_channel_id):
        """Initialize Tunnelling class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.udp_client = udp_client
        self.src_address = src_address

        super(Tunnelling, self).__init__(xknx, self.udp_client, TunnellingAck)

        self.telegram = telegram
        self.sequence_counter = sequence_counter
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self):
        """Create KNX/IP Frame object to be sent to device."""
        knxipframe = KNXIPFrame(self.xknx)
        knxipframe.init(KNXIPServiceType.TUNNELLING_REQUEST)
        knxipframe.body.communication_channel_id = self.communication_channel_id
        knxipframe.body.cemi.telegram = self.telegram
        knxipframe.body.cemi.src_addr = self.src_address
        knxipframe.body.sequence_counter = self.sequence_counter
        return knxipframe
