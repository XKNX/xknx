"""Abstraction to send SessionRequest and wait for SessionResponse."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import KNXIPFrame, SessionRequest, SessionResponse

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Session(RequestResponse):
    """Class to send a SessionRequest and wait for SessionResponse."""

    def __init__(
        self,
        transport: KNXIPTransport,
        ecdh_client_public_key: bytes,
    ):
        """Initialize Session class."""
        # TODO: increase timeout to timeoutAuthentication: 10sec ?
        super().__init__(transport, SessionResponse)
        self.ecdh_client_public_key = ecdh_client_public_key
        # TODO: make RequestResponse generic for response class
        # maybe replace self.success with self.response None check
        # remove on_success_hook in favour of using knxipframe.body directly
        self.response: SessionResponse | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(
            SessionRequest(ecdh_client_public_key=self.ecdh_client_public_key)
        )

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        assert isinstance(knxipframe.body, SessionResponse)
        self.response = knxipframe.body
