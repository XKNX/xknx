"""
Module for Serialization and Deserialization of a KNX Disconnect Request information.

Disconnect requests are used to disconnect a tunnel from a KNX/IP device.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class DisconnectRequest(KNXIPBody):
    """Representation of a KNX Disconnect Request."""

    SERVICE_TYPE = KNXIPServiceType.DISCONNECT_REQUEST

    def __init__(
        self,
        communication_channel_id: int = 1,
        control_endpoint: HPAI | None = None,
    ):
        """Initialize DisconnectRequest object."""
        self.communication_channel_id = communication_channel_id
        self.control_endpoint = control_endpoint or HPAI()

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < 2:
            raise CouldNotParseKNXIP("Disconnect info has wrong length")
        self.communication_channel_id = raw[0]
        # raw[1] is reserved
        return self.control_endpoint.from_knx(raw[2:]) + 2

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes((self.communication_channel_id, 0x00))  # 2nd byte is reserved
            + self.control_endpoint.to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<DisconnectRequest "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'control_endpoint="{self.control_endpoint}" />'
        )
