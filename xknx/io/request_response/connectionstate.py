"""Abstraction to send ConnectonStateRequest and wait for ConnectionStateResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.io.const import CONNECTIONSTATE_REQUEST_TIMEOUT
from xknx.knxip import HPAI, ConnectionStateRequest, ConnectionStateResponse, KNXIPFrame

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class ConnectionState(RequestResponse):
    """Class to send ConnectonStateRequest and wait for ConnectionStateResponse."""

    def __init__(
        self,
        transport: KNXIPTransport,
        communication_channel_id: int,
        local_hpai: HPAI,
    ):
        """Initialize ConnectionState class."""
        super().__init__(
            transport,
            ConnectionStateResponse,
            timeout_in_seconds=CONNECTIONSTATE_REQUEST_TIMEOUT,
        )
        self.communication_channel_id = communication_channel_id
        self.local_hpai = local_hpai

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        connectionstate_request = ConnectionStateRequest(
            communication_channel_id=self.communication_channel_id,
            control_endpoint=self.local_hpai,
        )
        return KNXIPFrame.init_from_body(connectionstate_request)
