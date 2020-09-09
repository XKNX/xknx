"""
Module for Serialization and Deserialization of KNX Search Response.

Search Requests are used to search for KNX/IP devices within the network.
A search response contains all information of a found device (Name, serial number, supported features.).
It supports an array-style access to the DIBs (use classname as index). Every KNXnet/ip server shall send
a search response and one device supporting multiple KNX connections may send multiple search responses.
"""
from .body import KNXIPBody
from .dib import DIB, DIBDeviceInformation
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class SearchResponse(KNXIPBody):
    """Representation of a KNX Search Response."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.SEARCH_RESPONSE

    def __init__(self, xknx):
        """Initialize SearchResponse object."""
        super().__init__(xknx)
        self.control_endpoint = HPAI()
        self.dibs = []

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return HPAI.LENGTH + sum([dib.calculated_length() for dib in self.dibs])

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.control_endpoint.from_knx(raw)
        while raw[pos:]:
            dib = DIB.determine_dib(raw[pos:])
            pos += dib.from_knx(raw[pos:])
            self.dibs.append(dib)
        return pos

    @property
    def device_name(self):
        """Return name of device."""
        for dib in self.dibs:
            if isinstance(dib, DIBDeviceInformation):
                return dib.name
        return "UNKNOWN"

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        data = []
        data.extend(self.control_endpoint.to_knx())
        for dib in self.dibs:
            data.extend(dib.to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<SearchResponse control_endpoint="{}" dibs="[\n{}\n]" />'.format(
            self.control_endpoint, ",\n".join(dib.__str__() for dib in self.dibs)
        )

    def __getitem__(self, clazz):
        """Return the first DIB of given class."""
        for dib in self.dibs:
            if isinstance(dib, clazz):
                return dib
        raise IndexError
