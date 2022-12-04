"""
Module for Serialization and Deserialization of KNX Session Requests.

The SESSION_REQUEST is used to initiate the secure connection setup
handshake for a new secure communication session.
"""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import HostProtocol, KNXIPServiceType


class SessionRequest(KNXIPBody):
    """Representation of a KNX Session Request."""

    SERVICE_TYPE = KNXIPServiceType.SESSION_REQUEST
    # 8 octets for the UDP/TCP HPAI and 32 octets for the client’s ECDH public value
    LENGTH: Final = 40

    def __init__(
        self,
        control_endpoint: HPAI | None = None,
        ecdh_client_public_key: bytes = bytes(32),
    ):
        """Initialize SessionRequest object."""
        self.control_endpoint = control_endpoint or HPAI(protocol=HostProtocol.IPV4_TCP)
        self.ecdh_client_public_key = ecdh_client_public_key

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return SessionRequest.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != SessionRequest.LENGTH:
            raise CouldNotParseKNXIP("SessionRequest has wrong length")
        pos = self.control_endpoint.from_knx(raw)
        self.ecdh_client_public_key = raw[pos:]
        return SessionRequest.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.control_endpoint.to_knx() + self.ecdh_client_public_key

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"<SessionRequest "
            f'control_endpoint="{self.control_endpoint}" '
            f'ecdh_client_public_key="{self.ecdh_client_public_key.hex()}" />'
        )
