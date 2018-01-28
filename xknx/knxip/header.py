"""Module for serialization and deserialization of KNX/IP Header."""
from xknx.exceptions import CouldNotParseKNXIP

from .body import KNXIPBody
from .knxip_enum import KNXIPServiceType


class KNXIPHeader():
    """Class for serialization and deserialization of KNX/IP Header."""

    HEADERLENGTH = 0x06
    PROTOCOLVERSION = 0x10

    def __init__(self, xknx):
        """Initialize KNXIPHeader class."""
        self.xknx = xknx
        self.header_length = KNXIPHeader.HEADERLENGTH
        self.protocol_version = KNXIPHeader.PROTOCOLVERSION
        self.service_type_ident = KNXIPServiceType.ROUTING_INDICATION
        self.b4_reserve = 0
        self.total_length = 0  # to be set later

    def from_knx(self, data):
        """Parse/deserialize from KNX/IP raw data."""
        if len(data) < KNXIPHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[0] != KNXIPHeader.HEADERLENGTH:
            raise CouldNotParseKNXIP("wrong connection header length")
        if data[1] != KNXIPHeader.PROTOCOLVERSION:
            raise CouldNotParseKNXIP("wrong protocol version")

        self.header_length = data[0]
        self.protocol_version = data[1]
        self.service_type_ident = KNXIPServiceType(data[2] * 256 + data[3])
        self.b4_reserve = data[4]
        self.total_length = data[5]
        return KNXIPHeader.HEADERLENGTH

    def set_length(self, body):
        """Set length of full KNX/IP packet from body + fixed header length."""
        if not isinstance(body, KNXIPBody):
            raise TypeError()
        self.total_length = KNXIPHeader.HEADERLENGTH + \
            body.calculated_length()

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        data = []
        data.append(self.header_length)
        data.append(self.protocol_version)
        data.append((self.service_type_ident.value >> 8) & 255)
        data.append(self.service_type_ident.value & 255)
        data.append((self.total_length >> 8) & 255)
        data.append(self.total_length & 255)
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<KNXIPHeader HeaderLength="{0}" ProtocolVersion="{1}" ' \
            'KNXIPServiceType="{2}" Reserve="{3}" TotalLength="{4}" />'.format(
                self.header_length,
                self.protocol_version,
                self.service_type_ident,
                self.b4_reserve,
                self.total_length)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
