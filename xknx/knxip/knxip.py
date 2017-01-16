from .knxip_enum import KNXIPServiceType
from .header import KNXIPHeader
from .cemi_frame import CEMIFrame
from .connect_request import ConnectRequest
from .connect_response import ConnectResponse
from .tunnelling_request import TunnellingRequest
from .tunnelling_ack import TunnellingAck
from .search_request import SearchRequest
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

        elif service_type_ident == \
                KNXIPServiceType.TUNNELLING_ACK:
            self.body = TunnellingAck()

        elif service_type_ident == \
                KNXIPServiceType.SEARCH_REQUEST:
            self.body = SearchRequest()

        else:
            raise TypeError(self.header.service_type_ident)


    def from_knx(self, data):

        pos = self.header.from_knx(data)

        self.init(self.header.service_type_ident)
        pos += self.body.from_knx(data[pos:])

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
