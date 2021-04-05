"""Abstraction to send ConnectonStateRequest and wait for ConnectionStateResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.io.const import CONNECTIONSTATE_REQUEST_TIMEOUT
from xknx.knxip import HPAI, ConnectionStateRequest, ConnectionStateResponse, KNXIPFrame

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.udp_client import UDPClient
    from xknx.xknx import XKNX


class ConnectionState(RequestResponse):
    """Class to send ConnectonStateRequest and wait for ConnectionStateResponse."""

    def __init__(
        self,
        xknx: XKNX,
        udp_client: UDPClient,
        communication_channel_id: int,
        route_back: bool = False,
    ):
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
