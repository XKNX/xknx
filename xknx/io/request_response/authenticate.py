"""Abstraction to send SessionAuthenticate and wait for SessionStatus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.io.const import SESSION_REQUEST_TIMEOUT
from xknx.knxip import KNXIPFrame, SessionAuthenticate, SessionStatus

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Authenticate(RequestResponse[SessionStatus]):
    """Class to send a SessionAuthenticate and wait for SessionStatus."""

    __slots__ = ("message_authentication_code", "user_id")

    def __init__(
        self,
        transport: KNXIPTransport,
        user_id: int,
        message_authentication_code: bytes,
    ) -> None:
        """Initialize Authenticate class."""
        # KNX v01.01.02 - KNX IP Secure 03.08.09 - §2.2.3.5.2.1.1 timeoutAuthentication
        super().__init__(transport, timeout_in_seconds=SESSION_REQUEST_TIMEOUT)
        self.user_id = user_id
        self.message_authentication_code = message_authentication_code

    def _create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(
            SessionAuthenticate(
                user_id=self.user_id,
                message_authentication_code=self.message_authentication_code,
            )
        )
