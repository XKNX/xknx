"""
Module for Serialization and Deserialization of a KNX Connetionstate Request information.

Connectionstate requests are used to determine if a tunnel connection is still active and valid.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class ConnectionStateRequest(KNXIPBody):
    """Representation of a KNX Connection State Request."""

    SERVICE_TYPE = KNXIPServiceType.CONNECTIONSTATE_REQUEST

    def __init__(
        self,
        communication_channel_id: int = 1,
        control_endpoint: HPAI | None = None,
    ):
        """Initialize ConnectionStateRequest object."""
        self.communication_channel_id = communication_channel_id
        self.control_endpoint = control_endpoint or HPAI()

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        def info_from_knx(info: bytes) -> int:
            """Parse info bytes."""
            if len(info) < 2:
                raise CouldNotParseKNXIP("Info has wrong length")
            self.communication_channel_id = info[0]
            # info[1] is reserved
            return 2

        pos = info_from_knx(raw)
        pos += self.control_endpoint.from_knx(raw[pos:])
        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes((self.communication_channel_id, 0x00))  # 2nd byte is reserved
            + self.control_endpoint.to_knx()
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<ConnectionStateRequest "
            f'communication_channel_id="{self.communication_channel_id}", '
            f'control_endpoint="{self.control_endpoint}" />'
        )
