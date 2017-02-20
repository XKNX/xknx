from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import ConnectRequestType, KNXIPServiceType
from .error_code import ErrorCode
from .exception import CouldNotParseKNXIP

class ConnectResponse(KNXIPBody):
    """Representation of a KNX Connect Request."""
    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.CONNECT_RESPONSE

    CRD_LENGTH = 4

    def __init__(self):
        """ConnectResponse __init__ object."""
        super(ConnectResponse, self).__init__()

        self.communication_channel = 0
        self.status_code = ErrorCode.E_NO_ERROR
        self.request_type = None
        self.control_endpoint = HPAI()
        self.identifier = None


    def calculated_length(self):
        return 2 + HPAI.LENGTH + \
           ConnectResponse.CRD_LENGTH

    def from_knx(self, raw):
        """Create a new ConnectResponse KNXIP raw data."""

        # CRD: Connection Response Data Block
        def crd_from_knx(crd):
            if crd[0] != ConnectResponse.CRD_LENGTH:
                raise CouldNotParseKNXIP("CRD has wrong length")
            if len(crd) < ConnectResponse.CRD_LENGTH:
                raise CouldNotParseKNXIP("CRD data has wrong length")
            self.request_type = ConnectRequestType(crd[1])
            self.identifier = crd[2]*256+crd[3]
            return 4

        self.communication_channel = raw[0]
        self.status_code = ErrorCode(raw[1])
        pos = 2

        pos += self.control_endpoint.from_knx(raw[pos:])
        pos += crd_from_knx(raw[pos:])
        return pos


    def to_knx(self):
        """Convert the ConnectResponse to its byte representation."""

        # CRD: Connection Response Data Block
        def crd_to_knx():
            crd = []
            crd.append(ConnectResponse.CRD_LENGTH)
            crd.append(self.request_type.value)
            crd.append((self.identifier >> 8) & 255)
            crd.append(self.identifier & 255)
            return crd

        data = []
        data.append(self.communication_channel)
        data.append(self.status_code.value)
        data.extend(self.control_endpoint.to_knx())
        data.extend(crd_to_knx())
        return data


    def __str__(self):
        return "<ConnectResponse communication_channel={0}, " \
            "status_code={1}, control_endpoint={2}, " \
            "request_type={3}, identifier={4}>" \
            .format(self.communication_channel, self.status_code,
                    self.control_endpoint, self.request_type,
                    self.identifier)
