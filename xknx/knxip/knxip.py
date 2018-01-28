"""
Module for serialization and deserialization of KNX/IP packets.

It consists of a header and a body.
Depending on the service_type_ident different types of body classes are instanciated.
"""
from xknx.exceptions import CouldNotParseKNXIP

from .cemi_frame import CEMIFrame
from .connect_request import ConnectRequest
from .connect_response import ConnectResponse
from .connectionstate_request import ConnectionStateRequest
from .connectionstate_response import ConnectionStateResponse
from .disconnect_request import DisconnectRequest
from .disconnect_response import DisconnectResponse
from .header import KNXIPHeader
from .knxip_enum import KNXIPServiceType
from .search_request import SearchRequest
from .search_response import SearchResponse
from .tunnelling_ack import TunnellingAck
from .tunnelling_request import TunnellingRequest


class KNXIPFrame:
    """Class for KNX/IP Frames."""

    def __init__(self, xknx):
        """Initialize object."""
        self.xknx = xknx
        self.header = KNXIPHeader(xknx)
        self.body = None

    def init(self, service_type_ident):
        """Init object by service_type_ident. Will instanciate a body object depending on service_type_ident."""
        self.header.service_type_ident = service_type_ident

        if service_type_ident == \
                KNXIPServiceType.ROUTING_INDICATION:
            self.body = CEMIFrame(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.CONNECT_REQUEST:
            self.body = ConnectRequest(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.CONNECT_RESPONSE:
            self.body = ConnectResponse(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.TUNNELLING_REQUEST:
            self.body = TunnellingRequest(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.TUNNELLING_ACK:
            self.body = TunnellingAck(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.SEARCH_REQUEST:
            self.body = SearchRequest(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.SEARCH_RESPONSE:
            self.body = SearchResponse(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.DISCONNECT_REQUEST:
            self.body = DisconnectRequest(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.DISCONNECT_RESPONSE:
            self.body = DisconnectResponse(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.CONNECTIONSTATE_REQUEST:
            self.body = ConnectionStateRequest(self.xknx)
        elif service_type_ident == \
                KNXIPServiceType.CONNECTIONSTATE_RESPONSE:
            self.body = ConnectionStateResponse(self.xknx)
        else:
            raise TypeError(self.header.service_type_ident)

    def from_knx(self, data):
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.header.from_knx(data)

        self.init(self.header.service_type_ident)
        pos += self.body.from_knx(data[pos:])

        if pos != len(data):
            raise CouldNotParseKNXIP("KNXIP data has wrong length")

        return pos

    def normalize(self):
        """Normalize internal data. Necessary step for serialization."""
        self.header.set_length(self.body)

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        data = []
        data.extend(self.header.to_knx())
        data.extend(self.body.to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<KNXIPFrame {0}\n body="{1}" />' \
            .format(self.header, self.body)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
