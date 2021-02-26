"""Abstraction to send ConnectRequest and wait for ConnectResponse."""
from typing import TYPE_CHECKING

from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestType,
    ConnectResponse,
    KNXIPFrame,
)

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.xknx import XKNX

    from .udp_client import UDPClient


class Connect(RequestResponse):
    """Class to send a ConnectRequest and wait for ConnectResponse.."""

    def __init__(
            self, xknx: "XKNX", 
            udp_client: "UDPClient",
            route_back: bool = False,
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            data_endpoint = None):
        """Initialize Connect class."""
        self.udp_client = udp_client
        self.route_back = route_back
        super().__init__(xknx, self.udp_client, ConnectResponse)
        self.communication_channel = 0
        self.identifier = 0
        self.request_type = request_type
        self.data_endpoint = data_endpoint

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        # set control_endpoint and data_endpoint to the same udp_connection
        if self.route_back:
            endpoint = HPAI()
        else:
            (local_addr, local_port) = self.udp_client.getsockname()
            endpoint = HPAI(ip_addr=local_addr, port=local_port)
        if not self.data_endpoint:
            self.data_endpoint = endpoint

        connect_request = ConnectRequest(
            self.xknx,
            request_type=self.request_type,
            control_endpoint=endpoint,
            data_endpoint=self.data_endpoint,
        )
        return KNXIPFrame.init_from_body(connect_request)

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        assert isinstance(knxipframe.body, ConnectResponse)
        assert isinstance(knxipframe.body.identifier, int)
        self.communication_channel = knxipframe.body.communication_channel
        self.identifier = knxipframe.body.identifier
