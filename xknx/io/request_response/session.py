"""Abstraction to send SessionRequest and wait for SessionResponse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import KNXIPFrame, SessionRequest, SessionResponse

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Session(RequestResponse[SessionResponse]):
    """Class to send a SessionRequest and wait for SessionResponse."""

    __slots__ = ("ecdh_client_public_key", "response")

    def __init__(
        self,
        transport: KNXIPTransport,
        ecdh_client_public_key: bytes,
    ) -> None:
        """Initialize Session class."""
        # TODO: increase timeout to timeoutAuthentication: 10sec ?
        super().__init__(transport)
        self.ecdh_client_public_key = ecdh_client_public_key
        # TODO: maybe replace self.success with self.response None check
        # and remove on_success_hook in favour of using self.response directly
        self.response: SessionResponse | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(
            SessionRequest(ecdh_client_public_key=self.ecdh_client_public_key)
        )

    def on_success_hook(self, response: SessionResponse) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        self.response = response
