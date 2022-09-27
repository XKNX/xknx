"""
Module for Serialization and Deserialization of KNX Timer Notify.

This frame shall be sent during secure KNXnet/IP multicast group communication
to keep the multicast group member's timer values synchronized.
"""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class TimerNotify(KNXIPBody):
    """Representation of a KNX Timer Notify."""

    SERVICE_TYPE = KNXIPServiceType.TIMER_NOTIFY
    LENGTH: Final = 30

    def __init__(
        self,
        timer_value: int = 0,
        serial_number: bytes = bytes(6),
        message_tag: bytes = bytes(2),
        message_authentication_code: bytes = bytes(16),
    ):
        """Initialize TimerNotify object."""
        self.timer_value = timer_value
        self.serial_number = serial_number
        self.message_tag = message_tag
        self.message_authentication_code = message_authentication_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return TimerNotify.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) != TimerNotify.LENGTH:
            raise CouldNotParseKNXIP("TimerNotify has wrong length")
        self.timer_value = int.from_bytes(raw[:6], "big")
        self.serial_number = raw[6:12]
        self.message_tag = raw[12:14]
        self.message_authentication_code = raw[14:]
        return TimerNotify.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            self.timer_value.to_bytes(6, "big")
            + self.serial_number
            + self.message_tag
            + self.message_authentication_code
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<TimerNotify "
            f'timer_value="{self.timer_value}" '
            f'serial_number="{self.serial_number.hex()}" '
            f'message_tag="{self.message_tag.hex()}" '
            f'message_authentication_code="{self.message_authentication_code.hex()}" />'
        )
