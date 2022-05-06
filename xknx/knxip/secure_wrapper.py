"""
Module for Serialization and Deserialization of KNX Secure Wrapper.

When KNXnet/IP frames are to be sent over a secured connection, each frame including
the KNXnet/IP header shall be completely encapsulated as encrypted payload inside a
SECURE_WRAPPER frame that adds some extra information needed to decrypt the frame and
for ensuring data integrity and freshness.
"""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType

# 2 octets secure session identifier
# 6 octets sequence information
# 6 octets KNX serial number
# 2 octets message tag
SECURITY_INFORMATION_LENGTH: Final = 16
# 6 octets for KNX/IP header
# 2 for smallest payload (eg. SessionStatus)
MINIMUM_PAYLOAD_LENGTH: Final = 2
MESSAGE_AUTHENTICATION_CODE_LENGTH: Final = 16

SECURE_WRAPPER_MINIMUM_LENGTH: Final = (
    SECURITY_INFORMATION_LENGTH
    + MINIMUM_PAYLOAD_LENGTH
    + MESSAGE_AUTHENTICATION_CODE_LENGTH
)


class SecureWrapper(KNXIPBody):
    """Representation of a KNX Secure Wrapper."""

    SERVICE_TYPE = KNXIPServiceType.SECURE_WRAPPER

    def __init__(
        self,
        secure_session_id: int = 0,
        sequence_information: bytes = bytes(6),
        serial_number: bytes = bytes(6),
        message_tag: bytes = bytes(2),
        encrypted_data: bytes = bytes(0),
        message_authentication_code: bytes = bytes(16),
    ):
        """Initialize SecureWrapper object."""
        self.secure_session_id = secure_session_id
        self.sequence_information = sequence_information
        self.serial_number = serial_number
        self.message_tag = message_tag
        self.encrypted_data = encrypted_data
        self.message_authentication_code = message_authentication_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return (
            SECURITY_INFORMATION_LENGTH
            + len(self.encrypted_data)
            + MESSAGE_AUTHENTICATION_CODE_LENGTH
        )

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < SECURE_WRAPPER_MINIMUM_LENGTH:
            raise CouldNotParseKNXIP("SecureWrapper has invalid length")
        self.secure_session_id = int.from_bytes(raw[:2], "big")
        self.sequence_information = raw[2:8]
        self.serial_number = raw[8:14]
        self.message_tag = raw[14:16]
        self.encrypted_data = raw[16:-MESSAGE_AUTHENTICATION_CODE_LENGTH]
        self.message_authentication_code = raw[-MESSAGE_AUTHENTICATION_CODE_LENGTH:]
        return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            self.secure_session_id.to_bytes(2, "big")
            + self.sequence_information
            + self.serial_number
            + self.message_tag
            + self.encrypted_data
            + self.message_authentication_code
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            f"<SecureWrapper "
            f'secure_session_id="{self.secure_session_id}" '
            f'sequence_information="{self.sequence_information.hex()}" '
            f'serial_number="{self.serial_number.hex()}" '
            f'message_tag="{self.message_tag.hex()}" '
            f'encrypted_data="{self.encrypted_data.hex()}" '
            f'message_authentication_code="{self.message_authentication_code.hex()}" />'
        )
