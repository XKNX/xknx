"""
Module for Serialization and Deserialization of a KNX Disconnect Request information.

Connect requests are used to disconnect a tunnel from a KNX/IP device.
"""
from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class DisconnectRequest(KNXIPBody):
    """Representation of a KNX Disconnect Request."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.DISCONNECT_REQUEST

    def __init__(self, xknx):
        """Initialize DisconnectRequest object."""
        super(DisconnectRequest, self).__init__(xknx)

        self.communication_channel_id = 1
        self.control_endpoint = HPAI()

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return 2 + HPAI.LENGTH

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        def info_from_knx(info):
            """Parse info bytes."""
            if len(info) < 2:
                raise CouldNotParseKNXIP("Disconnect info has wrong length")
            self.communication_channel_id = info[0]
            # info[1] is reserved
            return 2

        pos = info_from_knx(raw)
        pos += self.control_endpoint.from_knx(raw[pos:])
        return pos

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        def info_to_knx():
            """Serialize information bytes."""
            info = []
            info.append(self.communication_channel_id)
            info.append(0x00)  # Reserved
            return info
        data = []
        data.extend(info_to_knx())
        data.extend(self.control_endpoint.to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<DisconnectRequest CommunicationChannelID="{0}" ' \
            'control_endpoint="{1}" />'.format(
                self.communication_channel_id,
                self.control_endpoint)
