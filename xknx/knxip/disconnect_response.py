from .knxip_enum import KNXIPServiceType
from .body import KNXIPBody
from .exception import CouldNotParseKNXIP
from .error_code import ErrorCode

class DisconnectResponse(KNXIPBody):
    """Representation of a KNX Disconnect Response."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.DISCONNECT_RESPONSE

    def __init__(self):
        """DisconnectResponse __init__ object."""
        super(DisconnectResponse, self).__init__()

        self.communication_channel_id = 1
        self.status_code = ErrorCode.E_NO_ERROR

    def calculated_length(self):
        return 2


    def from_knx(self, raw):
        """Create a new DisconnectResponse KNXIP raw data."""

        def info_from_knx(info):
            if len(info) < 2:
                raise CouldNotParseKNXIP("Disconnect info has wrong length")
            self.communication_channel_id = info[0]
            self.status_code = ErrorCode(info[1])
            return 2

        pos = info_from_knx(raw)
        return pos


    def to_knx(self):
        """Convert the DisconnectResponse to its byte representation."""

        def info_to_knx():
            info = []
            info.append(self.communication_channel_id)
            info.append(self.status_code.value)
            return info

        data = []
        data.extend(info_to_knx())
        return data


    def __str__(self):
        return "<DisconnectResponse CommunicationChannelID={0}, " \
            "status_code={1}".format(
                self.communication_channel_id,
                self.status_code)
