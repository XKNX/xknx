"""Abstraction to send a TunnelingRequest and wait for TunnelingResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import KNXIPFrame, TunnellingAck, TunnellingRequest

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import UDPTransport


class Tunnelling(RequestResponse):
    """Class to send TunnelingRequest and wait for TunnelingACK (UDP only)."""

    transport: UDPTransport

    def __init__(
        self,
        transport: UDPTransport,
        data_endpoint: tuple[str, int] | None,
        tunnelling_request: TunnellingRequest,
    ):
        """Initialize Tunnelling class."""
        self.data_endpoint_addr = data_endpoint
        self.tunnelling_request = tunnelling_request
        super().__init__(transport, TunnellingAck)

    async def send_request(self) -> None:
        """Build knxipframe (within derived class) and send via UDP."""
        self.transport.send(self.create_knxipframe(), addr=self.data_endpoint_addr)

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(self.tunnelling_request)
