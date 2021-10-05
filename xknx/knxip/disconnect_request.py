"""
Module for Serialization and Deserialization of a KNX Disconnect Request information.

Disconnect requests are used to disconnect a tunnel from a KNX/IP device.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class DisconnectRequest(KNXIPBody):
    """Representation of a KNX Disconnect Request."""

    SERVICE_TYPE = KNXIPServiceType.DISCONNECT_REQUEST

    def __init__(
        self,
        xknx: XKNX,
        communication_channel_id: int = 1,
        control_endpoint: HPAI = HPAI(),
    ):
        """Initialize DisconnectRequest object."""
        super().__init__(xknx)

        self.communication_channel_id = communication_channel_id
        self.control_endpoint = control_endpoint

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        def info_from_knx(info: bytes) -> int:
            """Parse info bytes."""
            if len(info) < 2:
                raise CouldNotParseKNXIP("Disconnect info has wrong length")
            self.communication_channel_id = info[0]
            # info[1] is reserved
            return 2

        pos = info_from_knx(raw)
        pos += self.control_endpoint.from_knx(raw[pos:])
        return pos

    def to_knx(self) -> list[int]:
        """Serialize to KNX/IP raw data."""

        def info_to_knx() -> list[int]:
            """Serialize information bytes."""
            info = []
            info.append(self.communication_channel_id)
            info.append(0x00)  # Reserved
            return info

        data = []
        data.extend(info_to_knx())
        data.extend(self.control_endpoint.to_knx())
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<DisconnectRequest "
            f'CommunicationChannelID="{self.communication_channel_id}" '
            f'control_endpoint="{self.control_endpoint}" />'
        )
