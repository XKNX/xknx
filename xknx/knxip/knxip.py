"""
Module for serialization and deserialization of KNX/IP packets.

It consists of a header and a body.
Depending on the service_type_ident different types of body classes are instantiated.
"""
from __future__ import annotations

from xknx.exceptions import CouldNotParseKNXIP, IncompleteKNXIPFrame

from .body import KNXIPBody
from .connect_request import ConnectRequest
from .connect_response import ConnectResponse
from .connectionstate_request import ConnectionStateRequest
from .connectionstate_response import ConnectionStateResponse
from .description_request import DescriptionRequest
from .description_response import DescriptionResponse
from .disconnect_request import DisconnectRequest
from .disconnect_response import DisconnectResponse
from .header import KNXIPHeader
from .knxip_enum import KNXIPServiceType
from .routing_busy import RoutingBusy
from .routing_indication import RoutingIndication
from .routing_lost_message import RoutingLostMessage
from .search_request import SearchRequest
from .search_request_extended import SearchRequestExtended
from .search_response import SearchResponse
from .search_response_extended import SearchResponseExtended
from .secure_wrapper import SecureWrapper
from .session_authenticate import SessionAuthenticate
from .session_request import SessionRequest
from .session_response import SessionResponse
from .session_status import SessionStatus
from .timer_notify import TimerNotify
from .tunnelling_ack import TunnellingAck
from .tunnelling_request import TunnellingRequest


class KNXIPFrame:
    """Class for KNX/IP Frames."""

    def __init__(self, header: KNXIPHeader, body: KNXIPBody) -> None:
        """Initialize object."""
        self.header = header
        self.body = body

    @staticmethod
    def init_from_body(knxip_body: KNXIPBody) -> KNXIPFrame:
        """Return KNXIPFrame from KNXIPBody."""
        header = KNXIPHeader()
        header.service_type_ident = knxip_body.__class__.SERVICE_TYPE
        header.set_length(knxip_body)
        return KNXIPFrame(header=header, body=knxip_body)

    @staticmethod
    def from_knx(data: bytes) -> tuple[KNXIPFrame, bytes]:
        """
        Parse/deserialize from KNX/IP raw data.

        Returns a tuple of the KNXIPFrame and the rest of the data.

        Raises IncompleteKNXIPFrame if the data is not enough to parse the KNXIPFrame
        or CouldNotParseKNXIP on parsing error.
        """
        header = KNXIPHeader()
        pos_body = header.from_knx(data)
        if len(data) < header.total_length:
            raise IncompleteKNXIPFrame("Incomplete data for KNXIPFrame")
        # limit data to self.header.total_length for streaming socket data
        raw_body = data[pos_body : header.total_length]

        body: KNXIPBody
        # Core
        if header.service_type_ident == KNXIPServiceType.SEARCH_REQUEST:
            body = SearchRequest()
        elif header.service_type_ident == KNXIPServiceType.SEARCH_REQUEST_EXTENDED:
            body = SearchRequestExtended()
        elif header.service_type_ident == KNXIPServiceType.SEARCH_RESPONSE:
            body = SearchResponse()
        elif header.service_type_ident == KNXIPServiceType.SEARCH_RESPONSE_EXTENDED:
            body = SearchResponseExtended()
        elif header.service_type_ident == KNXIPServiceType.DESCRIPTION_REQUEST:
            body = DescriptionRequest()
        elif header.service_type_ident == KNXIPServiceType.DESCRIPTION_RESPONSE:
            body = DescriptionResponse()
        elif header.service_type_ident == KNXIPServiceType.CONNECT_REQUEST:
            body = ConnectRequest()
        elif header.service_type_ident == KNXIPServiceType.CONNECT_RESPONSE:
            body = ConnectResponse()
        elif header.service_type_ident == KNXIPServiceType.CONNECTIONSTATE_REQUEST:
            body = ConnectionStateRequest()
        elif header.service_type_ident == KNXIPServiceType.CONNECTIONSTATE_RESPONSE:
            body = ConnectionStateResponse()
        elif header.service_type_ident == KNXIPServiceType.DISCONNECT_REQUEST:
            body = DisconnectRequest()
        elif header.service_type_ident == KNXIPServiceType.DISCONNECT_RESPONSE:
            body = DisconnectResponse()
        # Tunneling
        elif header.service_type_ident == KNXIPServiceType.TUNNELLING_REQUEST:
            body = TunnellingRequest()
        elif header.service_type_ident == KNXIPServiceType.TUNNELLING_ACK:
            body = TunnellingAck()
        # Routing
        elif header.service_type_ident == KNXIPServiceType.ROUTING_INDICATION:
            body = RoutingIndication()
        elif header.service_type_ident == KNXIPServiceType.ROUTING_BUSY:
            body = RoutingBusy()
        elif header.service_type_ident == KNXIPServiceType.ROUTING_LOST_MESSAGE:
            body = RoutingLostMessage()
        # Secure
        elif header.service_type_ident == KNXIPServiceType.SECURE_WRAPPER:
            body = SecureWrapper()
        elif header.service_type_ident == KNXIPServiceType.SESSION_AUTHENTICATE:
            body = SessionAuthenticate()
        elif header.service_type_ident == KNXIPServiceType.SESSION_REQUEST:
            body = SessionRequest()
        elif header.service_type_ident == KNXIPServiceType.SESSION_RESPONSE:
            body = SessionResponse()
        elif header.service_type_ident == KNXIPServiceType.SESSION_STATUS:
            body = SessionStatus()
        elif header.service_type_ident == KNXIPServiceType.TIMER_NOTIFY:
            body = TimerNotify()
        else:
            raise CouldNotParseKNXIP(
                f"KNXIPServiceType not implemented: {header.service_type_ident.name}"
            )
        body.from_knx(raw_body)
        return KNXIPFrame(header=header, body=body), data[header.total_length :]

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.header.to_knx() + self.body.to_knx()

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<KNXIPFrame {self.header} body="{self.body}" />'

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
