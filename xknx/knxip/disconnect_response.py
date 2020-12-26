"""
Module for Serialization and Deserialization of a KNX Disconnect Response information.

Disconnect requests are used to disconnect a tunnel from a KNX/IP device.
With a Disconnect Response the receiving party acknowledges the valid processing of the request.
"""
from typing import TYPE_CHECKING, List

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBodyResponse
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class DisconnectResponse(KNXIPBodyResponse):
    """Representation of a KNX Disconnect Response."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.DISCONNECT_RESPONSE

    def __init__(
        self,
        xknx: "XKNX",
        communication_channel_id: int = 1,
        status_code: ErrorCode = ErrorCode.E_NO_ERROR,
    ):
        """Initialize DisconnectResponse object."""
        super().__init__(xknx)

        self.communication_channel_id = communication_channel_id
        self.status_code = status_code

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return 2

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""

        def info_from_knx(info: bytes) -> int:
            """Parse info bytes."""
            if len(info) < 2:
                raise CouldNotParseKNXIP("Disconnect info has wrong length")
            self.communication_channel_id = info[0]
            self.status_code = ErrorCode(info[1])
            return 2

        pos = info_from_knx(raw)
        return pos

    def to_knx(self) -> List[int]:
        """Serialize to KNX/IP raw data."""

        def info_to_knx() -> List[int]:
            """Serialize information bytes."""
            info = []
            info.append(self.communication_channel_id)
            info.append(self.status_code.value)
            return info

        data = []
        data.extend(info_to_knx())
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<DisconnectResponse CommunicationChannelID="{}" '
            'status_code="{}" />'.format(
                self.communication_channel_id, self.status_code
            )
        )
