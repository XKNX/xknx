"""
Module for Serialization and Deserialization of KNX Search Requests.

Search Requests are used to search for KNX/IP devices within the network.
"""
from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class SearchRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.SEARCH_REQUEST

    def __init__(self, xknx):
        """Initialize SearchRequest object."""
        super(SearchRequest, self).__init__(xknx)
        self.discovery_endpoint = HPAI(ip_addr="224.0.23.12", port=3671)

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return HPAI.LENGTH

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.discovery_endpoint.from_knx(raw)
        return pos

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        data = []
        data.extend(self.discovery_endpoint.to_knx())
        return data

    def __str__(self):
        """Return object as readable string."""
        return '<SearchRequest discovery_endpoint="{0}" />' \
            .format(self.discovery_endpoint)
