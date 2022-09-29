"""
Module for Serialization and Deserialization of KNX RoutingBusy frames.

RoutingBusy frames are used for flow control.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class RoutingBusy(KNXIPBody):
    """Representation of a KNX RoutingBusy frame."""

    SERVICE_TYPE = KNXIPServiceType.ROUTING_BUSY
    BODY_LENGTH = 6

    def __init__(
        self,
        device_state: int = 0,
        wait_time: int = 100,
        control_field: int = 0,
    ):
        """Initialize RoutingBusy object."""
        self.device_state = device_state
        self.wait_time = wait_time
        self.control_field = control_field

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return RoutingBusy.BODY_LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if raw[0] != RoutingBusy.BODY_LENGTH:  # structure_length field
            raise CouldNotParseKNXIP("RoutingBusy body has invalid length")
        if len(raw) != RoutingBusy.BODY_LENGTH:
            raise CouldNotParseKNXIP("RoutingBusy has wrong length")
        self.device_state = raw[1]
        self.wait_time = raw[2] * 256 + raw[3]
        self.control_field = raw[4] * 256 + raw[5]
        return RoutingBusy.BODY_LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes((RoutingBusy.BODY_LENGTH, self.device_state))
            + self.wait_time.to_bytes(2, "big")
            + self.control_field.to_bytes(2, "big")
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<RoutingBusy "
            f"device_state={self.device_state} "
            f"wait_time={self.wait_time} "
            f"control_field={self.control_field} />"
        )
