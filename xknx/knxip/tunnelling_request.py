from .body import KNXIPBody
from .exception import CouldNotParseKNXIP
from .cemi_frame import CEMIFrame, CEMIMessageCode
from .knxip_enum import KNXIPServiceType


class TunnellingRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.TUNNELLING_REQUEST

    HEADER_LENGTH = 4

    def __init__(self):
        """TunnellingRequest __init__ object."""
        super(TunnellingRequest, self).__init__()

        self.communication_channel_id = 1
        self.sequence_counter = 0
        self.cemi = CEMIFrame()
        self.cemi.code = CEMIMessageCode.L_Data_REQ

    def calculated_length(self):
        return TunnellingRequest.HEADER_LENGTH + \
            self.cemi.calculated_length()


    def from_knx(self, raw):
        """Create a new TunnellingRequest KNXIP raw data."""

        def header_from_knx(header):
            if header[0] != TunnellingRequest.HEADER_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            if len(header) < TunnellingRequest.HEADER_LENGTH:
                raise CouldNotParseKNXIP("connection header wrong length")
            self.communication_channel_id = header[1]
            self.sequence_counter = header[2]
            return 4

        pos = header_from_knx(raw)

        pos += self.cemi.from_knx(raw[pos:])

        return pos

    def to_knx(self):
        """Convert the TunnellingRequest to its byte representation."""

        def header_to_knx():
            cri = []
            cri.append(TunnellingRequest.HEADER_LENGTH)
            cri.append(self.communication_channel_id)
            cri.append(self.sequence_counter)
            cri.append(0x00) # Reserved
            return cri

        data = []
        data.extend(header_to_knx())
        data.extend(self.cemi.to_knx())
        return data


    def __str__(self):
        return "<TunnellingRequest communication_channel_id={0}, " \
            "sequence_counter={1}, cemi={2}>" \
            .format(self.communication_channel_id,
                    self.sequence_counter,
                    self.cemi)
