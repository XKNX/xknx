"""
Module for Serialization and Deserialization of a KNX Connectionstate Response information.

Connectionstate requests are used to determine if a tunnel connection is still active and valid.
With a connectionstate response the receiving party acknowledges the valid processing of the request.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType


class ConnectionStateResponse(KNXIPBodyResponse):
    """Representation of a KNX Connection State Response."""

    SERVICE_TYPE = KNXIPServiceType.CONNECTIONSTATE_RESPONSE
    LENGTH = 2

    def __init__(
        self,
        communication_channel_id: int = 1,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
    ):
        """Initialize ConnectionStateResponse object."""
        self.communication_channel_id = communication_channel_id
        self.status_code = status_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return ConnectionStateResponse.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < ConnectionStateResponse.LENGTH:
            raise CouldNotParseKNXIP("ConnectionStateResponse info has wrong length")
        self.communication_channel_id = raw[0]
        self.status_code = ErrorCode(raw[1])
        return ConnectionStateResponse.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return bytes((self.communication_channel_id, self.status_code.value))

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<ConnectionStateResponse "
            f'communication_channel_id="{self.communication_channel_id}" '
            f'status_code="{self.status_code}" />'
        )
