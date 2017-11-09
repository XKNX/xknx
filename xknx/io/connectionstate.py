"""Abstraction to send ConnectonStateRequest and wait for ConnectionStateResponse."""
from xknx.knxip import (HPAI, ConnectionStateResponse, KNXIPFrame,
                        KNXIPServiceType)

from .request_response import RequestResponse


class ConnectionState(RequestResponse):
    """Class to send ConnectonStateRequest and wait for ConnectionStateResponse."""

    def __init__(self, xknx, udp_client, communication_channel_id):
        """Initialize ConnectionState class."""
        self.udp_client = udp_client
        super(ConnectionState, self).__init__(xknx, self.udp_client, ConnectionStateResponse)
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self):
        """Create KNX/IP Frame object to be sent to device."""
        (local_addr, local_port) = self.udpclient.getsockname()
        knxipframe = KNXIPFrame(self.xknx)
        knxipframe.init(KNXIPServiceType.CONNECTIONSTATE_REQUEST)
        knxipframe.body.communication_channel_id = \
            self.communication_channel_id
        knxipframe.body.control_endpoint = HPAI(
            ip_addr=local_addr, port=local_port)

        return knxipframe
