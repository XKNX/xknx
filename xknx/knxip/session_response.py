"""
Module for Serialization and Deserialization of KNX Session Responses.

The SESSION_RESPONSE shall be sent by the KNXnet/IP secure server to the secure
client's control endpoint in response to a received secure session request frame.
"""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class SessionResponse(KNXIPBody):
    """Representation of a KNX Session Response."""

    SERVICE_TYPE = KNXIPServiceType.SESSION_RESPONSE
    # 2 octets secure session identifier
    # 32 octets for the servers’s ECDH public value
    # 16 octets for the message authentication code
    LENGTH: Final = 50

    def __init__(
        self,
        secure_session_id: int = 0,
        ecdh_server_public_key: bytes = bytes(32),
        message_authentication_code: bytes = bytes(16),
    ):
        """Initialize SessionResponse object."""
        self.ecdh_server_public_key = ecdh_server_public_key
        # secure session identifier 0 shall in general be reserved for
        # multicast data and shall not be used for unicast connections
        self.secure_session_id = secure_session_id
        self.message_authentication_code = message_authentication_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return SessionResponse.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != SessionResponse.LENGTH:
            raise CouldNotParseKNXIP("SessionResponse has wrong length")
        self.secure_session_id = int.from_bytes(raw[:2], "big")
        self.ecdh_server_public_key = raw[2:34]
        self.message_authentication_code = raw[34:]
        return SessionResponse.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            self.secure_session_id.to_bytes(2, "big")
            + self.ecdh_server_public_key
            + self.message_authentication_code
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"<SessionResponse "
            f'secure_session_id="{self.secure_session_id}" '
            f'ecdh_server_public_key="{self.ecdh_server_public_key.hex()}" '
            f'message_authentication_code="{self.message_authentication_code.hex()}" />'
        )
