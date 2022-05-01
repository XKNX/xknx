"""Abstraction to send SessionAuthenticate and wait for SessionStatus."""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.knxip import KNXIPFrame, SessionAuthenticate, SessionStatus

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Authenticate(RequestResponse):
    """Class to send a SessionAuthenticate and wait for SessionStatus."""

    def __init__(
        self,
        transport: KNXIPTransport,
        user_id: int,
        message_authentication_code: bytes,
    ):
        """Initialize Session class."""
        super().__init__(transport, SessionStatus, timeout_in_seconds=10)
        self.user_id = user_id
        self.message_authentication_code = message_authentication_code
        self.response: SessionStatus | None = None

    def create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(
            SessionAuthenticate(
                user_id=self.user_id,
                message_authentication_code=self.message_authentication_code,
            )
        )

    def on_success_hook(self, knxipframe: KNXIPFrame) -> None:
        """Set communication channel and identifier after having received a valid answer."""
        assert isinstance(knxipframe.body, SessionStatus)
        self.response = knxipframe.body
