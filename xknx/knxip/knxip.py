from .knxip_enum import KNXIPServiceType
from .header import KNXIPHeader
from .cemi_frame import CEMIFrame
from .connect_request import ConnectRequest
from .connect_response import ConnectResponse
from .tunnelling_request import TunnellingRequest
from .exception import CouldNotParseKNXIP

class KNXIPFrame:
    """Abstraction for KNX IP Frames"""


    def __init__(self):
        """Initialize object."""
        self.header = KNXIPHeader()
        self.body = None


    def init(self, service_type_ident):
        self.header.service_type_ident = service_type_ident

        # pylint: disable=redefined-variable-type
        if service_type_ident == \
                KNXIPServiceType.ROUTING_INDICATION:
            self.body = CEMIFrame()
        elif service_type_ident == \
                KNXIPServiceType.CONNECT_REQUEST:
            self.body = ConnectRequest()
        elif service_type_ident == \
                KNXIPServiceType.CONNECT_RESPONSE:
            self.body = ConnectResponse()
        elif service_type_ident == \
                KNXIPServiceType.TUNNELLING_REQUEST:
            self.body = TunnellingRequest()
        else:
            raise TypeError()


    def from_knx(self, data):

        pos = self.header.from_knx(data)

        # pylint: disable=redefined-variable-type
        if self.header.service_type_ident == \
                KNXIPServiceType.ROUTING_INDICATION:
            self.body = CEMIFrame()
            pos += self.body.from_knx(data[pos:])

        elif self.header.service_type_ident == \
                KNXIPServiceType.CONNECT_REQUEST:
            self.body = ConnectRequest()
            pos += self.body.from_knx(data[pos:])

        elif self.header.service_type_ident == \
                KNXIPServiceType.CONNECT_RESPONSE:
            self.body = ConnectResponse()
            pos += self.body.from_knx(data[pos:])

        elif self.header.service_type_ident == \
                KNXIPServiceType.TUNNELLING_REQUEST:
            self.body = TunnellingRequest()
            pos += self.body.from_knx(data[pos:])

        else:
            raise TypeError()

        if pos != len(data):
            raise CouldNotParseKNXIP("KNXIP data has wrong length")

    def __str__(self):
        return "<KNXIPFrame {0}\n body={1}>" \
            .format(self.header, self.body)


    def normalize(self):
        self.header.set_length(self.body)

    def to_knx(self):

        data = []
        data.extend(self.header.to_knx())
        data.extend(self.body.to_knx())
        return data
