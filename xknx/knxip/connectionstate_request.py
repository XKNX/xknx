from .knxip_enum import KNXIPServiceType
from .body import KNXIPBody
from .hpai import HPAI
from .exception import CouldNotParseKNXIP


class ConnectionStateRequest(KNXIPBody):
    """Representation of a KNX Connection State Request."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.CONNECTIONSTATE_REQUEST

    def __init__(self):
        """ConnectionStateRequest __init__ object."""
        super(ConnectionStateRequest, self).__init__()

        self.communication_channel_id = 1
        self.control_endpoint = HPAI()

    def calculated_length(self):
        return 2 + HPAI.LENGTH


    def from_knx(self, raw):
        """Create a new ConnectionStateRequest KNXIP raw data."""

        def info_from_knx(info):
            if len(info) < 2:
                raise CouldNotParseKNXIP("Info has wrong length")
            self.communication_channel_id = info[0]
            # info[1] is reserved
            return 2

        pos = info_from_knx(raw)
        pos += self.control_endpoint.from_knx(raw[pos:])
        return pos


    def to_knx(self):
        """Convert the ConnectionStateRequest to its byte representation."""

        def info_to_knx():
            info = []
            info.append(self.communication_channel_id)
            info.append(0x00) # Reserved
            return info

        data = []
        data.extend(info_to_knx())
        data.extend(self.control_endpoint.to_knx())
        return data


    def __str__(self):
        return "<ConnectionStateRequest CommunicationChannelID={0}, " \
            "control_endpoint={1}".format(
                self.communication_channel_id,
                self.control_endpoint)
