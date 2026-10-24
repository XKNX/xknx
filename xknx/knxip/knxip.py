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
from .device_configuration_ack import DeviceConfigurationAck
from .device_configuration_request import DeviceConfigurationRequest
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
from .tunnelling_feature import (
    TunnellingFeatureGet,
    TunnellingFeatureInfo,
    TunnellingFeatureResponse,
    TunnellingFeatureSet,
)
from .tunnelling_request import TunnellingRequest

# KNX/IP body class per service type - the service types xknx implements
_BODY_CLASSES: dict[KNXIPServiceType, type[KNXIPBody]] = {
    body_class.SERVICE_TYPE: body_class
    for body_class in (
        # Core
        SearchRequest,
        SearchRequestExtended,
        SearchResponse,
        SearchResponseExtended,
        DescriptionRequest,
        DescriptionResponse,
        ConnectRequest,
        ConnectResponse,
        ConnectionStateRequest,
        ConnectionStateResponse,
        DisconnectRequest,
        DisconnectResponse,
        # Device Management
        DeviceConfigurationRequest,
        DeviceConfigurationAck,
        # Tunnelling
        TunnellingRequest,
        TunnellingAck,
        TunnellingFeatureGet,
        TunnellingFeatureInfo,
        TunnellingFeatureResponse,
        TunnellingFeatureSet,
        # Routing
        RoutingIndication,
        RoutingBusy,
        RoutingLostMessage,
        # Secure
        SecureWrapper,
        SessionAuthenticate,
        SessionRequest,
        SessionResponse,
        SessionStatus,
        TimerNotify,
    )
}


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

        try:
            body = _BODY_CLASSES[header.service_type_ident]()
        except KeyError:
            raise CouldNotParseKNXIP(
                f"KNXIPServiceType not implemented: {header.service_type_ident.name}"
            ) from None
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
