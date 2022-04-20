"""
Module for Serialization and Deserialization of KNX Session Authenticates.

The SESSION_AUTHENTICATE shall be sent by the KNXnet/IP secure client to the
control endpoint of the KNXnet/IP secure server after the Diffie-Hellman handshake
to authenticate the user against the server device.
"""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class SessionAuthenticate(KNXIPBody):
    """Representation of a KNX Session Authenticate."""

    SERVICE_TYPE = KNXIPServiceType.SESSION_AUTHENTICATE
    LENGTH: Final = 18

    def __init__(
        self,
        user_id: int = 0x02,
        message_authentication_code: bytes = bytes(16),
    ):
        """Initialize SessionAuthenticate object."""
        # 00h: Reserved, shall not be used
        # 01h: Management level access
        # 02h – 7Fh: User level access
        # 80h – FFh: Reserved, shall not be used
        # TODO: maybe use an Enum instead of int or raise an error in
        #   to_knx() and handle in RequestResponse class
        self.user_id = user_id
        self.message_authentication_code = message_authentication_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return SessionAuthenticate.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != SessionAuthenticate.LENGTH:
            raise CouldNotParseKNXIP("SessionAuthenticate has wrong length")
        self.user_id = raw[1]
        self.message_authentication_code = raw[2:]
        return SessionAuthenticate.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes(
                (
                    0x00,  # reserved
                    self.user_id,
                )
            )
            + self.message_authentication_code
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"<SessionAuthenticate "
            f'user_id="{self.user_id}" '
            f'message_authentication_code="{self.message_authentication_code.hex()}" />'
        )
