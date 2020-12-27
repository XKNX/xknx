"""
Module for Serialization and Deserialization of a KNX Connetionstate Request information.

Connectionstate requests are used to determine if a tunnel connection is still active and valid.
"""
from typing import TYPE_CHECKING, List

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class ConnectionStateRequest(KNXIPBody):
    """Representation of a KNX Connection State Request."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.CONNECTIONSTATE_REQUEST

    def __init__(
        self,
        xknx: "XKNX",
        communication_channel_id: int = 1,
        control_endpoint: HPAI = HPAI(),
    ):
        """Initialize ConnectionStateRequest object."""
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
                raise CouldNotParseKNXIP("Info has wrong length")
            self.communication_channel_id = info[0]
            # info[1] is reserved
            return 2

        pos = info_from_knx(raw)
        pos += self.control_endpoint.from_knx(raw[pos:])
        return pos

    def to_knx(self) -> List[int]:
        """Serialize to KNX/IP raw data."""

        def info_to_knx() -> List[int]:
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
            '<ConnectionStateRequest CommunicationChannelID="{}", '
            'control_endpoint="{}" />'.format(
                self.communication_channel_id, self.control_endpoint
            )
        )
