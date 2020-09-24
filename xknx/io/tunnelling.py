"""Abstraction to send a TunnelingRequest and wait for TunnelingResponse."""
from xknx.knxip import (
    CEMIFrame,
    CEMIMessageCode,
    KNXIPFrame,
    TunnellingAck,
    TunnellingRequest,
)

from .request_response import RequestResponse


class Tunnelling(RequestResponse):
    """Class to TunnelingRequest and wait for TunnelingResponse."""

    def __init__(
        self,
        xknx,
        udp_client,
        telegram,
        src_address,
        sequence_counter,
        communication_channel_id,
    ):
        """Initialize Tunnelling class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.udp_client = udp_client
        self.src_address = src_address

        super().__init__(xknx, self.udp_client, TunnellingAck)

        self.telegram = telegram
        self.sequence_counter = sequence_counter
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        cemi = CEMIFrame.init_from_telegram(
            self.xknx,
            telegram=self.telegram,
            code=CEMIMessageCode.L_Data_REQ,
            src_addr=self.src_address,
        )
        tunnelling_request = TunnellingRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            sequence_counter=self.sequence_counter,
            cemi=cemi,
        )
        return KNXIPFrame.init_from_body(tunnelling_request)
