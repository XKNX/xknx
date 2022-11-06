"""
Module for Serialization and Deserialization of KNX Search Requests.

Search Requests are used to search for KNX/IP devices within the network.
"""
from __future__ import annotations

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class SearchRequest(KNXIPBody):
    """Representation of a KNX Search Request."""

    SERVICE_TYPE = KNXIPServiceType.SEARCH_REQUEST

    def __init__(self, discovery_endpoint: HPAI | None = None):
        """Initialize SearchRequest object."""
        self.discovery_endpoint = discovery_endpoint or HPAI()

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        return self.discovery_endpoint.from_knx(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.discovery_endpoint.to_knx()

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<SearchRequest discovery_endpoint="{self.discovery_endpoint}" />'
