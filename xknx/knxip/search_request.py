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

    def __init__(self, xknx, discovery_endpoint: HPAI = None):
        """Initialize SearchRequest object."""
        super().__init__(xknx)
        self.discovery_endpoint = (
            discovery_endpoint
            if discovery_endpoint is not None
            else HPAI(ip_addr=xknx.multicast_group, port=xknx.multicast_port)
        )

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
        return '<SearchRequest discovery_endpoint="{}" />'.format(
            self.discovery_endpoint
        )
