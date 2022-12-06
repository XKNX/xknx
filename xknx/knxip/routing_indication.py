"""
Module for Serialization and Deserialization of KNX RoutingIndication frames.

Routing indications are used to transport CEMI Messages.
"""
from __future__ import annotations

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class RoutingIndication(KNXIPBody):
    """Representation of a KNX RoutingIndication frame."""

    SERVICE_TYPE = KNXIPServiceType.ROUTING_INDICATION

    def __init__(self, raw_cemi: bytes = b""):
        """Initialize RoutingIndication object."""
        self.raw_cemi = raw_cemi

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return len(self.raw_cemi)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        self.raw_cemi = raw
        return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.raw_cemi

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<RoutingIndication cemi="{self.raw_cemi.hex()}" />'
