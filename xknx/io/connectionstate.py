"""Abstraction to send ConnectonStateRequest and wait for ConnectionStateResponse."""
from xknx.knxip import HPAI, ConnectionStateRequest, ConnectionStateResponse, KNXIPFrame

from .const import CONNECTIONSTATE_REQUEST_TIMEOUT
from .request_response import RequestResponse


class ConnectionState(RequestResponse):
    """Class to send ConnectonStateRequest and wait for ConnectionStateResponse."""

    def __init__(self, xknx, udp_client, communication_channel_id, route_back):
        """Initialize ConnectionState class."""
        self.udp_client = udp_client
        self.route_back = route_back
        super().__init__(
            xknx, 
            self.udp_client, 
            ConnectionStateResponse,
            timeout_in_seconds=CONNECTIONSTATE_REQUEST_TIMEOUT,
        )
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        if self.route_back:
            endpoint = HPAI()
        else:
            (local_addr, local_port) = self.udpclient.getsockname()
            endpoint = HPAI(ip_addr=local_addr, port=local_port)
        connectionstate_request = ConnectionStateRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            control_endpoint=endpoint,
        )
        return KNXIPFrame.init_from_body(connectionstate_request)
