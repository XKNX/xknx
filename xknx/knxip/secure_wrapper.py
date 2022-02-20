"""
Module for Serialization and Deserialization of KNX Secure Wrapper.

When KNXnet/IP frames are to be sent over a secured connection, each frame including
the KNXnet/IP header shall be completely encapsulated as encrypted payload inside a
SECURE_WRAPPER frame that adds some extra information needed to decrypt the frame and
for ensuring data integrity and freshness.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX

# 2 octets secure session identifier
# 6 octets sequence information
# 6 octets KNX serial number
# 2 octets message tag
SECURITY_INFORMATION_LENGTH: Final = 16
# 6 octets for KNX/IP header
# 2 for smallest payload (eg. SessionStatus)
# 16 for message authentication code
MINIMUM_PAYLOAD_LENGTH: Final = 24


class SecureWrapper(KNXIPBody):
    """Representation of a KNX Secure Wrapper."""

    SERVICE_TYPE = KNXIPServiceType.SECURE_WRAPPER

    def __init__(
        self,
        xknx: XKNX,
        secure_session_id: int = 0,
        sequence_information: int = 0,
        serial_number: int = 0,
        message_tag: int = 0,
        encrypted_data: bytes = bytes(0),
    ):
        """Initialize SecureWrapper object."""
        super().__init__(xknx)
        self.secure_session_id = secure_session_id
        self.sequence_information = sequence_information
        self.serial_number = serial_number
        self.message_tag = message_tag
        self.encrypted_data = encrypted_data

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return SECURITY_INFORMATION_LENGTH + len(self.encrypted_data)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < (SECURITY_INFORMATION_LENGTH + MINIMUM_PAYLOAD_LENGTH):
            raise CouldNotParseKNXIP("SecureWrapper has invalid length")
        self.secure_session_id = int.from_bytes(raw[:2], "big")
        self.sequence_information = int.from_bytes(raw[2:8], "big")
        self.serial_number = int.from_bytes(raw[8:14], "big")
        self.message_tag = int.from_bytes(raw[14:16], "big")
        self.encrypted_data = raw[16:]
        return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            self.secure_session_id.to_bytes(2, "big")
            + self.sequence_information.to_bytes(6, "big")
            + self.serial_number.to_bytes(6, "big")
            + self.message_tag.to_bytes(2, "big")
            + self.encrypted_data
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f"<SecureWrapper "
            f'secure_session_id="{self.secure_session_id}" '
            f'sequence_information="{self.sequence_information}" '
            f'serial_number="{self.serial_number}" '
            f'message_tag="{self.message_tag}" '
            f"encrypted_data={self.encrypted_data.hex()} />"
        )
