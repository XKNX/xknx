"""Abstraction to send ConnectRequest and wait for ConnectResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestInformation,
    ConnectResponse,
    KNXIPFrame,
)
from xknx.telegram import IndividualAddress

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Connect(RequestResponse):
    """
    Class to send a ConnectRequest and wait for ConnectResponse.

    Setting a `individual_address` is only supported for Tunnelling v2 connections.
    """

    def __init__(
        self,
        transport: KNXIPTransport,
        local_hpai: HPAI,
        individual_address: IndividualAddress | None = None,
    ):
        """Initialize Connect class."""
        super().__init__(transport, ConnectResponse)
        self.communication_channel = 0
        self.data_endpoint = HPAI()
        self.identifier = 0
        self.individual_address = individual_address
        self.local_hpai = local_hpai

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        cri = ConnectRequestInformation(individual_address=self.individual_address)
        # use the same HPAI for control_endpoint and data_endpoint
        connect_request = ConnectRequest(
            control_endpoint=self.local_hpai,
            data_endpoint=self.local_hpai,
            cri=cri,
        )
        return KNXIPFrame.init_from_body(connect_request)

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        assert isinstance(knxipframe.body, ConnectResponse)
        self.communication_channel = knxipframe.body.communication_channel
        self.data_endpoint = knxipframe.body.data_endpoint
        self.identifier = knxipframe.body.identifier
