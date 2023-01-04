"""Module for serialization and deserialization of KNX/IP Header."""
from __future__ import annotations

from typing import Final

from xknx.exceptions import CouldNotParseKNXIP, IncompleteKNXIPFrame

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class KNXIPHeader:
    """Class for serialization and deserialization of KNX/IP Header."""

    HEADERLENGTH: Final = 0x06
    PROTOCOLVERSION: Final = 0x10  # The only valid protocol version at this time is 1.0

    def __init__(self) -> None:
        """Initialize KNXIPHeader class."""
        self.service_type_ident = KNXIPServiceType.ROUTING_INDICATION
        self.total_length = 0  # to be set later

    def from_knx(self, data: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(data) < KNXIPHeader.HEADERLENGTH:
            raise IncompleteKNXIPFrame("wrong connection header length")
        if data[0] != KNXIPHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        # set immediately, as we need it for tcp stream parsing before raising exception
        self.total_length = data[4] * 256 + data[5]
        if data[1] != KNXIPHeader.PROTOCOLVERSION:
            raise CouldNotParseKNXIP("wrong protocol version")

        try:
            self.service_type_ident = KNXIPServiceType(data[2] * 256 + data[3])
        except ValueError:
            raise CouldNotParseKNXIP(f"KNXIPServiceType unknown: 0x{data[2:4].hex()}")
        return KNXIPHeader.HEADERLENGTH

    def set_length(self, body: KNXIPBody) -> None:
        """Set length of full KNX/IP packet from body + fixed header length."""
        if not isinstance(body, KNXIPBody):
            raise TypeError()
        self.total_length = KNXIPHeader.HEADERLENGTH + body.calculated_length()

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return (
            bytes((KNXIPHeader.HEADERLENGTH, KNXIPHeader.PROTOCOLVERSION))
            + self.service_type_ident.value.to_bytes(2, "big")
            + self.total_length.to_bytes(2, "big")
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<KNXIPHeader "
            f'HeaderLength="{KNXIPHeader.HEADERLENGTH}" '
            f'ProtocolVersion="{KNXIPHeader.PROTOCOLVERSION}" '
            f'KNXIPServiceType="{self.service_type_ident.name}" '
            f'TotalLength="{self.total_length}" />'
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
