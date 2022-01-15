"""Abstraction to send a TunnelingRequest and wait for TunnelingResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import (
    CEMIFrame,
    CEMIMessageCode,
    KNXIPFrame,
    TunnellingAck,
    TunnellingRequest,
)

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import UDPTransport
    from xknx.telegram import IndividualAddress, Telegram
    from xknx.xknx import XKNX


class Tunnelling(RequestResponse):
    """Class to TunnelingRequest and wait for TunnelingACK (UDP only)."""

    transport: UDPTransport

    def __init__(
        self,
        xknx: XKNX,
        transport: UDPTransport,
        data_endpoint: tuple[str, int] | None,
        telegram: Telegram,
        src_address: IndividualAddress,
        sequence_counter: int,
        communication_channel_id: int,
    ):
        """Initialize Tunnelling class."""
        self.data_endpoint_addr = data_endpoint
        self.src_address = src_address

        super().__init__(xknx, transport, TunnellingAck)

        self.telegram = telegram
        self.sequence_counter = sequence_counter
        self.communication_channel_id = communication_channel_id

    async def send_request(self) -> None:
        """Build knxipframe (within derived class) and send via UDP."""
        self.transport.send(self.create_knxipframe(), addr=self.data_endpoint_addr)

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        cemi = CEMIFrame.init_from_telegram(
            self.xknx,
            telegram=self.telegram,
            code=CEMIMessageCode.L_DATA_REQ,
            src_addr=self.src_address,
        )
        tunnelling_request = TunnellingRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            sequence_counter=self.sequence_counter,
            cemi=cemi,
        )
        return KNXIPFrame.init_from_body(tunnelling_request)
