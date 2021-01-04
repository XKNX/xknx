"""Abstraction to send DisconnectRequest and wait for DisconnectResponse."""
from typing import TYPE_CHECKING

from xknx.knxip import HPAI, DisconnectRequest, DisconnectResponse, KNXIPFrame

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.xknx import XKNX

    from .udp_client import UDPClient


class Disconnect(RequestResponse):
    """Class to send a DisconnectRequest and wait for a DisconnectResponse."""

    def __init__(
        self, xknx: "XKNX", udp_client: "UDPClient", communication_channel_id: int
    ):
        """Initialize Disconnect class."""
        self.xknx = xknx
        self.udp_client = udp_client
        super().__init__(xknx, self.udp_client, DisconnectResponse)
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        (local_addr, local_port) = self.udpclient.getsockname()
        disconnect_request = DisconnectRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            control_endpoint=HPAI(ip_addr=local_addr, port=local_port),
        )
        return KNXIPFrame.init_from_body(disconnect_request)
