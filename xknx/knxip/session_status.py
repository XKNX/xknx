"""
Module for Serialization and Deserialization of KNX Session Status.

A SESSION_STATUS may be sent by the KNXnet/IP secure server to the KNXnet/IP secure client
or by the KNXnet/IP secure client to the KNXnet/IP secure server in any stage of the
secure session handshake to indicate an error condition or status information.
"""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType, SecureSessionStatusCode


class SessionStatus(KNXIPBody):
    """Representation of a KNX Session Status."""

    SERVICE_TYPE = KNXIPServiceType.SESSION_STATUS
    LENGTH: Final = 2

    def __init__(
        self,
        status: SecureSessionStatusCode = SecureSessionStatusCode.STATUS_KEEPALIVE,
    ):
        """Initialize SessionStatus object."""
        self.status = status

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return SessionStatus.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != SessionStatus.LENGTH:
            raise CouldNotParseKNXIP("SessionStatus has wrong length")
        try:
            self.status = SecureSessionStatusCode(raw[0])
        except ValueError as err:
            raise CouldNotParseKNXIP(
                f"SessionStatus has unsupported status code: {raw[0]}"
            ) from err
        return SessionStatus.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes(
            (
                self.status.value,
                0x00,  # reserved
            )
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<SessionStatus status="{self.status}" />'
