"""
Module for Serialization and Deserialization of KNX RoutingLostMessage frames.

RoutingLostMessage frames are used for system supervision.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class RoutingLostMessage(KNXIPBody):
    """Representation of a KNX RoutingLostMessage frame."""

    SERVICE_TYPE = KNXIPServiceType.ROUTING_LOST_MESSAGE
    BODY_LENGTH = 4

    def __init__(
        self,
        device_state: int = 0,
        lost_messages: int = 1,
    ):
        """Initialize RoutingLostMessage object."""
        self.device_state = device_state
        self.lost_messages = lost_messages

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return RoutingLostMessage.BODY_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if raw[0] != RoutingLostMessage.BODY_LENGTH:  # structure_length field
            raise CouldNotParseKNXIP("RoutingLostMessage body has invalid length")
        if len(raw) != RoutingLostMessage.BODY_LENGTH:
            raise CouldNotParseKNXIP("RoutingLostMessage has wrong length")
        self.device_state = raw[1]
        self.lost_messages = raw[2] * 256 + raw[3]
        return RoutingLostMessage.BODY_LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes(
            (RoutingLostMessage.BODY_LENGTH, self.device_state)
        ) + self.lost_messages.to_bytes(2, "big")

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<RoutingLostMessage "
            f"device_state={self.device_state} "
            f"lost_messages={self.lost_messages} />"
        )
