"""Abstraction to send ConnectonStateRequest and wait for ConnectionStateResponse."""
from xknx.knxip import (
    HPAI, ConnectionStateResponse, KNXIPFrame, KNXIPServiceType)

from .request_response import RequestResponse


class ConnectionState(RequestResponse):
    """Class to send ConnectonStateRequest and wait for ConnectionStateResponse."""

    def __init__(self, xknx, udp_client, communication_channel_id):
        """Initialize ConnectionState class."""
        self.udp_client = udp_client
        super().__init__(xknx, self.udp_client, ConnectionStateResponse)
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self):
        """Create KNX/IP Frame object to be sent to device."""
        if self.udp_client.proxy_addr[0] is None:
            (return_ip, return_port) = self.udp_client.getsockname()
        else:
            (return_ip, return_port) = self.udp_client.proxy_addr

        knxipframe = KNXIPFrame(self.xknx)
        knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        knxipframe.body.communication_channel_id = \
            self.communication_channel_id
        knxipframe.body.control_endpoint = HPAI(
            ip_addr=return_ip, port=return_port)

        return knxipframe
