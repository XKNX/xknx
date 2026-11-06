"""Abstraction to send SessionRequest and wait for SessionResponse."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.io.const import SESSION_REQUEST_TIMEOUT
from xknx.knxip import KNXIPFrame, SessionRequest, SessionResponse

from .request_response import RequestResponse

if TYPE_CHECKING:
    from xknx.io.transport import KNXIPTransport


class Session(RequestResponse[SessionResponse]):
    """Class to send a SessionRequest and wait for SessionResponse."""

    __slots__ = ("ecdh_client_public_key",)

    def __init__(
        self,
        transport: KNXIPTransport,
        ecdh_client_public_key: bytes,
    ) -> None:
        """Initialize Session class."""
        # KNX v01.01.02 - KNX IP Secure 03.08.09 - §2.2.3.5.2.1.1 timeoutAuthentication
        super().__init__(transport, timeout_in_seconds=SESSION_REQUEST_TIMEOUT)
        self.ecdh_client_public_key = ecdh_client_public_key

    def _create_knxipframe(self) -> KNXIPFrame:
        """Create KNX/IP Frame object to be sent to device."""
        return KNXIPFrame.init_from_body(
            SessionRequest(ecdh_client_public_key=self.ecdh_client_public_key)
        )
