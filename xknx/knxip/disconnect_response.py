from .body import KNXIPBody
from .exception import CouldNotParseKNXIP
from .error_code import ErrorCode

class DisconnectResponse(KNXIPBody):
    """Representation of a KNX Disconnect Response."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """DisconnectResponse __init__ object."""
        super(DisconnectResponse, self).__init__()

        self.communication_channel_id = 1
        self.status_code = ErrorCode.E_NO_ERROR

    def calculated_length(self):
        return 2


    def from_knx(self, raw):
        """Create a new DisconnectResponse KNXIP raw data."""

        def disconn_info_from_knx(disconn_info):
            if len(disconn_info) < 2:
                raise CouldNotParseKNXIP("Disconnect info has wrong length")
            self.communication_channel_id = disconn_info[0]
            self.status_code = ErrorCode(disconn_info[1])
            return 2

        pos = disconn_info_from_knx(raw)
        return pos


    def to_knx(self):
        """Convert the DisconnectResponse to its byte representation."""

        def disconn_info_to_knx():
            disconn_info = []
            disconn_info.append(self.communication_channel_id)
            disconn_info.append(self.status_code.value)
            return disconn_info

        data = []
        data.extend(disconn_info_to_knx())
        return data


    def __str__(self):
        return "<DisconnectResponse CommunicationChannelID={0}, " \
            "status_code={1}".format(
                self.communication_channel_id,
                self.status_code)
