"""
Module for Serialization and Deserialization of a KNX Disconnect Response information.

Disconnect requests are used to disconnect a tunnel from a KNX/IP device.
With a Disconnect Response the receiving party acknowledges the valid processing of the request.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType


class DisconnectResponse(KNXIPBodyResponse):
    """Representation of a KNX Disconnect Response."""

    SERVICE_TYPE = KNXIPServiceType.DISCONNECT_RESPONSE
    LENGTH = 2

    def __init__(
        self,
        communication_channel_id: int = 1,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
    ):
        """Initialize DisconnectResponse object."""
        self.communication_channel_id = communication_channel_id
        self.status_code = status_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return DisconnectResponse.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < DisconnectResponse.LENGTH:
            raise CouldNotParseKNXIP("Disconnect info has wrong length")
        self.communication_channel_id = raw[0]
        self.status_code = ErrorCode(raw[1])
        return DisconnectResponse.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes(
            (
                self.communication_channel_id,
                self.status_code.value,
            )
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<DisconnectResponse "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'status_code="{self.status_code}" />'
        )
