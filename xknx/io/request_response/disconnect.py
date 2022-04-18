"""Abstraction to send DisconnectRequest and wait for DisconnectResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import HPAI, DisconnectRequest, DisconnectResponse, KNXIPFrame

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Disconnect(RequestResponse):
    """Class to send a DisconnectRequest and wait for a DisconnectResponse."""

    def __init__(
        self,
        transport: KNXIPTransport,
        communication_channel_id: int,
        local_hpai: HPAI,
    ):
        """Initialize Disconnect class."""
        super().__init__(transport, DisconnectResponse)
        self.communication_channel_id = communication_channel_id
        self.local_hpai = local_hpai

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        disconnect_request = DisconnectRequest(
            communication_channel_id=self.communication_channel_id,
            control_endpoint=self.local_hpai,
        )
        return KNXIPFrame.init_from_body(disconnect_request)
