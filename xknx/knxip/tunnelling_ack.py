from .body import KNXIPBody
from .exception import CouldNotParseKNXIP
from .error_code import ErrorCode
from .knxip_enum import KNXIPServiceType


class TunnellingAck(KNXIPBody):
    """Representation of a KNX Connect Request."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.TUNNELLING_ACK

    BODY_LENGTH = 4

    def __init__(self):
        """TunnellingAck __init__ object."""
        super(TunnellingAck, self).__init__()

        self.communication_channel_id = 1
        self.sequence_counter = 0
        self.status_code = ErrorCode.E_NO_ERROR


    def calculated_length(self):
        return TunnellingAck.BODY_LENGTH


    def from_knx(self, raw):
        """Create a new TunnellingAck KNXIP raw data."""


        def ack_from_knx(header):
            if header[0] != TunnellingAck.BODY_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            if len(header) < TunnellingAck.BODY_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            self.communication_channel_id = header[1]
            self.sequence_counter = header[2]
            self.status_code = ErrorCode(header[3])
            return 4

        pos = ack_from_knx(raw)

        return pos


    def to_knx(self):
        """Convert the TunnellingAck to its byte representation."""

        def ack_to_knx():
            ack = []
            ack.append(TunnellingAck.BODY_LENGTH)
            ack.append(self.communication_channel_id)
            ack.append(self.sequence_counter)
            ack.append(self.status_code.value)
            return ack

        data = []
        data.extend(ack_to_knx())
        return data


    def __str__(self):
        return "<TunnellingAck communication_channel_id={0}, " \
            "sequence_counter={1}, status_code={2}>" \
            .format(self.communication_channel_id, self.sequence_counter,
                    self.status_code)
