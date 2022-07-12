"""Abstraction to send a TunnelingRequest and wait for TunnelingResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import CEMIFrame, KNXIPFrame, TunnellingAck, TunnellingRequest

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import UDPTransport


class Tunnelling(RequestResponse):
    """Class to TunnelingRequest and wait for TunnelingACK (UDP only)."""

    transport: UDPTransport

    def __init__(
        self,
        transport: UDPTransport,
        data_endpoint: tuple[str, int] | None,
        cemi: CEMIFrame,
        sequence_counter: int,
        communication_channel_id: int,
    ):
        """Initialize Tunnelling class."""
        self.data_endpoint_addr = data_endpoint

        super().__init__(transport, TunnellingAck)

        self.cemi_frame = cemi
        self.sequence_counter = sequence_counter
        self.communication_channel_id = communication_channel_id

    async def send_request(self) -> None:
        """Build knxipframe (within derived class) and send via UDP."""
        self.transport.send(self.create_knxipframe(), addr=self.data_endpoint_addr)

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        tunnelling_request = TunnellingRequest(
            communication_channel_id=self.communication_channel_id,
            sequence_counter=self.sequence_counter,
            cemi=self.cemi_frame,
        )
        return KNXIPFrame.init_from_body(tunnelling_request)
