"""Abstraction to send DisconnectRequest and wait for DisconnectResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import HPAI, DisconnectRequest, DisconnectResponse, KNXIPFrame

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.udp_client import UDPClient
    from xknx.xknx import XKNX


class Disconnect(RequestResponse):
    """Class to send a DisconnectRequest and wait for a DisconnectResponse."""

    def __init__(
        self,
        xknx: XKNX,
        udp_client: UDPClient,
        communication_channel_id: int,
        route_back: bool = False,
    ):
        """Initialize Disconnect class."""
        self.xknx = xknx
        self.udp_client = udp_client
        self.route_back = route_back
        super().__init__(xknx, self.udp_client, DisconnectResponse)
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        if self.route_back:
            endpoint = HPAI()
        else:
            (local_addr, local_port) = self.udpclient.getsockname()
            endpoint = HPAI(ip_addr=local_addr, port=local_port)
        disconnect_request = DisconnectRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            control_endpoint=endpoint,
        )
        return KNXIPFrame.init_from_body(disconnect_request)
