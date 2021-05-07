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
from xknx.telegram.telegram import TPDUType
from xknx.knxip.tpdu import TPDU
#from xknx.knxip import TPDUType

if TYPE_CHECKING:
    from xknx.io.udp_client import UDPClient
    from xknx.telegram import IndividualAddress, Telegram
    from xknx.xknx import XKNX


class Tunnelling(RequestResponse):
    """Class to TunnelingRequest and wait for TunnelingResponse."""

    def __init__(
        self,
        xknx: XKNX,
        udp_client: UDPClient,
        telegram: Telegram,
        src_address: IndividualAddress,
        sequence_counter: int,
        communication_channel_id: int,
    ):
        """Initialize Tunnelling class."""
        self.xknx = xknx
        self.udp_client = udp_client
        self.src_address = src_address

        super().__init__(xknx, self.udp_client, TunnellingAck)

        self.telegram = telegram
        self.sequence_counter = sequence_counter
        self.communication_channel_id = communication_channel_id

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent on bus."""
        if self.telegram.tpdu_type == TPDUType.T_DATA:
            pdu = CEMIFrame.init_from_telegram(
                self.xknx,
                telegram=self.telegram,
                code=CEMIMessageCode.L_DATA_REQ,
                src_addr=self.src_address,
            )
        else:
            # all other tpdu_types are non CEMI types
            pdu = TPDU.init_from_telegram(
                self.xknx,
                telegram=self.telegram,
                src_addr=self.src_address,)

        tunnelling_request = TunnellingRequest(
            self.xknx,
            communication_channel_id=self.communication_channel_id,
            sequence_counter=self.sequence_counter,
            cemi=pdu,
        )
        return KNXIPFrame.init_from_body(tunnelling_request)
