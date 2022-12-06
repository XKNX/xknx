"""
Module for Serialization and Deserialization of a KNX Tunnelling Request information.

Tunnelling requests are used to transmit a KNX telegram within an existing KNX tunnel connection.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class TunnellingRequest(KNXIPBody):
    """Representation of a KNX Tunnelling Request."""

    SERVICE_TYPE = KNXIPServiceType.TUNNELLING_REQUEST
    HEADER_LENGTH = 4

    def __init__(
        self,
        communication_channel_id: int = 1,
        sequence_counter: int = 0,
        raw_cemi: bytes = b"",
    ):
        """Initialize TunnellingRequest object."""
        self.communication_channel_id = communication_channel_id
        self.sequence_counter = sequence_counter
        self.raw_cemi = raw_cemi

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return TunnellingRequest.HEADER_LENGTH + len(self.raw_cemi)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if raw[0] != TunnellingRequest.HEADER_LENGTH:
            raise CouldNotParseKNXIP("connection header wrong length")
        if len(raw) < TunnellingRequest.HEADER_LENGTH:
            raise CouldNotParseKNXIP("connection header wrong length")
        self.communication_channel_id = raw[1]
        self.sequence_counter = raw[2]
        # raw[3] is reserved
        self.raw_cemi = raw[TunnellingRequest.HEADER_LENGTH :]
        return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes(
                (
                    TunnellingRequest.HEADER_LENGTH,
                    self.communication_channel_id,
                    self.sequence_counter,
                    0x00,  # Reserved
                )
            )
            + self.raw_cemi
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<TunnellingRequest "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'sequence_counter="{self.sequence_counter}" '
            f'cemi="{self.raw_cemi.hex()}" />'
        )
