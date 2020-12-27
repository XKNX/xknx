"""Abstraction to send ConnectonStateRequest and wait for ConnectionStateResponse."""
from typing import TYPE_CHECKING

from xknx.knxip import HPAI, ConnectionStateRequest, ConnectionStateResponse, KNXIPFrame

from .const import CONNECTIONSTATE_REQUEST_TIMEOUT
from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.xknx import XKNX

    from .udp_client import UDPClient


class ConnectionState(RequestResponse):
    """Class to send ConnectonStateRequest and wait for ConnectionStateResponse."""

    def __init__(
        self, xknx: "XKNX", udp_client: "UDPClient", communication_channel_id: int
    ):
        """Initialize ConnectionState class."""
        self.udp_client = udp_client
        super().__init__(
            xknx,
            self.udp_client,
            ConnectionStateResponse,
            timeout_in_seconds=CONNECTIONSTATE_REQUEST_TIMEOUT,
        )
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        (local_addr, local_port) = self.udpclient.getsockname()
        connectionstate_request = ConnectionStateRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            control_endpoint=HPAI(ip_addr=local_addr, port=local_port),
        )
        return KNXIPFrame.init_from_body(connectionstate_request)
