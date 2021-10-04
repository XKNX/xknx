"""Module for serialization and deserialization of KNX/IP Header."""
from __future__ import annotations

from typing import ClassVar

from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class KNXIPHeader:
    """Class for serialization and deserialization of KNX/IP Header."""

    HEADERLENGTH: ClassVar[int] = 0x06
    PROTOCOLVERSION: ClassVar[int] = 0x10

    def __init__(self) -> None:
        """Initialize KNXIPHeader class."""
        self.header_length = KNXIPHeader.HEADERLENGTH
        self.protocol_version = KNXIPHeader.PROTOCOLVERSION
        self.service_type_ident = KNXIPServiceType.ROUTING_INDICATION
        self.b4_reserve = 0
        self.total_length = 0  # to be set later

    def from_knx(self, data: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(data) < KNXIPHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[0] != KNXIPHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[1] != KNXIPHeader.PROTOCOLVERSION:
            raise CouldNotParseKNXIP("wrong protocol version")

        self.header_length = data[0]
        self.protocol_version = data[1]
        try:
            self.service_type_ident = KNXIPServiceType(data[2] * 256 + data[3])
        except ValueError:
            raise CouldNotParseKNXIP(
                f"KNXIPServiceType unknown: {hex(data[2] * 256 + data[3])}"
            )
        self.b4_reserve = data[4]
        self.total_length = data[5]
        return KNXIPHeader.HEADERLENGTH

    def set_length(self, body: KNXIPBody) -> None:
        """Set length of full KNX/IP packet from body + fixed header length."""
        if not isinstance(body, KNXIPBody):
            raise TypeError()
        self.total_length = KNXIPHeader.HEADERLENGTH + body.calculated_length()

    def to_knx(self) -> list[int]:
        """Serialize to KNX/IP raw data."""
        data = []
        data.append(self.header_length)
        data.append(self.protocol_version)
        data.append((self.service_type_ident.value >> 8) & 255)
        data.append(self.service_type_ident.value & 255)
        data.append((self.total_length >> 8) & 255)
        data.append(self.total_length & 255)
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            "<KNXIPHeader "
            f'HeaderLength="{self.header_length}" '
            f'ProtocolVersion="{self.protocol_version}" '
            f'KNXIPServiceType="{self.service_type_ident.name}" '
            f'Reserve="{self.b4_reserve}" '
            f'TotalLength="{self.total_length}" />'
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
