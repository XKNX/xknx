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
    from xknx.io.transport import KNXIPTransport


class Connect(RequestResponse):
    """Class to send a ConnectRequest and wait for ConnectResponse."""

    def __init__(
        self,
        transport: KNXIPTransport,
        local_hpai: HPAI,
    ):
        """Initialize Connect class."""
        super().__init__(transport, ConnectResponse)
        self.communication_channel = 0
        self.data_endpoint = HPAI()
        self.identifier = 0
        self.local_hpai = local_hpai

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        # use the same HPAI for control_endpoint and data_endpoint
        connect_request = ConnectRequest(
            request_type=ConnectRequestType.TUNNEL_CONNECTION,
            control_endpoint=self.local_hpai,
            data_endpoint=self.local_hpai,
        )
        return KNXIPFrame.init_from_body(connect_request)

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        assert isinstance(knxipframe.body, ConnectResponse)
        self.communication_channel = knxipframe.body.communication_channel
        self.data_endpoint = knxipframe.body.data_endpoint
        self.identifier = knxipframe.body.identifier
