"""
Module for Serialization and Deserialization of a KNX Disconnect Response information.

Disconnect requests are used to disconnect a tunnel from a KNX/IP device.
With a Disconnect Response the receiving party acknowledges the valid processing of the request.
"""
from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType


class DisconnectResponse(KNXIPBody):
    """Representation of a KNX Disconnect Response."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.DISCONNECT_RESPONSE

    def __init__(self, xknx):
        """Initialize DisconnectResponse object."""
        super(DisconnectResponse, self).__init__(xknx)

        self.communication_channel_id = 1
        self.status_code = ErrorCode.E_NO_ERROR

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return 2

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        def info_from_knx(info):
            """Parse info bytes."""
            if len(info) < 2:
                raise CouldNotParseKNXIP("Disconnect info has wrong length")
            self.communication_channel_id = info[0]
            self.status_code = ErrorCode(info[1])
            return 2
        pos = info_from_knx(raw)
        return pos

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        def info_to_knx():
            """Serialize information bytes."""
            info = []
            info.append(self.communication_channel_id)
            info.append(self.status_code.value)
            return info
        data = []
        data.extend(info_to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<DisconnectResponse CommunicationChannelID="{0}" ' \
            'status_code="{1}" />'.format(
                self.communication_channel_id,
                self.status_code)
