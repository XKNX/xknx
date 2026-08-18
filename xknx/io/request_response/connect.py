"""Abstraction to send ConnectRequest and wait for ConnectResponse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import (
    HPAI,
    ConnectRequest,
    ConnectRequestInformation,
    ConnectResponse,
    ConnectResponseData,
    KNXIPFrame,
)

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Connect(RequestResponse[ConnectResponse]):
    """
    Class to send a ConnectRequest and wait for ConnectResponse.

    Setting a `individual_address` is only supported for Tunnelling v2 connections.
    """

    __slots__ = ("communication_channel", "crd", "cri", "data_endpoint", "local_hpai")

    def __init__(
        self,
        transport: KNXIPTransport,
        local_hpai: HPAI,
        cri: ConnectRequestInformation | None = None,
    ) -> None:
        """Initialize Connect class."""
        super().__init__(transport)
        self.communication_channel = 0
        self.data_endpoint = HPAI()
        self.local_hpai = local_hpai
        self.cri = cri or ConnectRequestInformation()
        self.crd = ConnectResponseData()

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        # use the same HPAI for control_endpoint and data_endpoint
        connect_request = ConnectRequest(
            control_endpoint=self.local_hpai,
            data_endpoint=self.local_hpai,
            cri=self.cri,
        )
        return KNXIPFrame.init_from_body(connect_request)

    def on_success_hook(self, response: ConnectResponse) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        self.communication_channel = response.communication_channel
        self.data_endpoint = response.data_endpoint
        self.crd = response.crd
