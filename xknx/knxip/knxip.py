"""
Module for serialization and deserialization of KNX/IP packets.

It consists of a header and a body.
Depending on the service_type_ident different types of body classes are instanciated.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .connect_request import ConnectRequest
from .connect_response import ConnectResponse
from .connectionstate_request import ConnectionStateRequest
from .connectionstate_response import ConnectionStateResponse
from .disconnect_request import DisconnectRequest
from .disconnect_response import DisconnectResponse
from .header import KNXIPHeader
from .knxip_enum import KNXIPServiceType
from .routing_indication import RoutingIndication
from .search_request import SearchRequest
from .search_response import SearchResponse
from .tunnelling_ack import TunnellingAck
from .tunnelling_request import TunnellingRequest


class KNXIPFrame:
    """Class for KNX/IP Frames."""

    def __init__(self) -> None:
        """Initialize object."""
        self.header = KNXIPHeader()
        self.body: KNXIPBody | None = None

    def init(self, service_type_ident: KNXIPServiceType) -> KNXIPBody:
        """Init object by service_type_ident. Will instanciate a body object depending on service_type_ident."""
        self.header.service_type_ident = service_type_ident

        body: KNXIPBody
        if service_type_ident == KNXIPServiceType.ROUTING_INDICATION:
            body = RoutingIndication()
        elif service_type_ident == KNXIPServiceType.CONNECT_REQUEST:
            body = ConnectRequest()
        elif service_type_ident == KNXIPServiceType.CONNECT_RESPONSE:
            body = ConnectResponse()
        elif service_type_ident == KNXIPServiceType.TUNNELLING_REQUEST:
            body = TunnellingRequest()
        elif service_type_ident == KNXIPServiceType.TUNNELLING_ACK:
            body = TunnellingAck()
        elif service_type_ident == KNXIPServiceType.SEARCH_REQUEST:
            body = SearchRequest()
        elif service_type_ident == KNXIPServiceType.SEARCH_RESPONSE:
            body = SearchResponse()
        elif service_type_ident == KNXIPServiceType.DISCONNECT_REQUEST:
            body = DisconnectRequest()
        elif service_type_ident == KNXIPServiceType.DISCONNECT_RESPONSE:
            body = DisconnectResponse()
        elif service_type_ident == KNXIPServiceType.CONNECTIONSTATE_REQUEST:
            body = ConnectionStateRequest()
        elif service_type_ident == KNXIPServiceType.CONNECTIONSTATE_RESPONSE:
            body = ConnectionStateResponse()
        else:
            raise CouldNotParseKNXIP(
                f"KNXIPServiceType not implemented: {service_type_ident.name}"
            )
        self.body = body
        return body

    @staticmethod
    def init_from_body(knxip_body: KNXIPBody) -> KNXIPFrame:
        """Return KNXIPFrame from KNXIPBody."""
        knxipframe = KNXIPFrame()
        knxipframe.header.service_type_ident = knxip_body.__class__.SERVICE_TYPE
        knxipframe.body = knxip_body
        knxipframe.header.set_length(knxip_body)
        return knxipframe

    def from_knx(self, data: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.header.from_knx(data)

        pos += self.init(self.header.service_type_ident).from_knx(data[pos:])

        if pos != len(data):
            raise CouldNotParseKNXIP("KNXIP data has wrong length")

        return pos

    def to_knx(self) -> list[int]:
        """Serialize to KNX/IP raw data."""
        if self.body is None:
            raise CouldNotParseKNXIP("No body defined in KNXIPFrame.")
        data = []
        data.extend(self.header.to_knx())
        data.extend(self.body.to_knx())
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<KNXIPFrame {self.header}\n body="{self.body}" />'

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
