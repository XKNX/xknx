"""Abstraction to send ConnectRequest and wait for ConnectResponse."""
from __future__ import annotations

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
    from xknx.io.udp_client import UDPClient
    from xknx.xknx import XKNX


class Connect(RequestResponse):
    """Class to send a ConnectRequest and wait for ConnectResponse.."""

    def __init__(self, xknx: XKNX, udp_client: UDPClient, route_back: bool = False):
        """Initialize Connect class."""
        self.udp_client = udp_client
        self.route_back = route_back
        super().__init__(xknx, self.udp_client, ConnectResponse)
        self.communication_channel = 0
        self.identifier = 0

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        # set control_endpoint and data_endpoint to the same udp_connection
        if self.route_back:
            endpoint = HPAI()
        else:
            (local_addr, local_port) = self.udp_client.getsockname()
            endpoint = HPAI(ip_addr=local_addr, port=local_port)
        connect_request = ConnectRequest(
            self.xknx,
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            control_endpoint=endpoint,
            data_endpoint=endpoint,
        )
        return KNXIPFrame.init_from_body(connect_request)

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        assert isinstance(knxipframe.body, ConnectResponse)
        assert isinstance(knxipframe.body.identifier, int)
        self.communication_channel = knxipframe.body.communication_channel
        self.identifier = knxipframe.body.identifier
