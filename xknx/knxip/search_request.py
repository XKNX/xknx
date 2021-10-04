"""
Module for Serialization and Deserialization of KNX Search Requests.

Search Requests are used to search for KNX/IP devices within the network.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class SearchRequest(KNXIPBody):
    """Representation of a KNX Connect Request."""

    SERVICE_TYPE = KNXIPServiceType.SEARCH_REQUEST

    def __init__(self, xknx: XKNX, discovery_endpoint: HPAI | None = None):
        """Initialize SearchRequest object."""
        super().__init__(xknx)
        self.discovery_endpoint = (
            discovery_endpoint
            if discovery_endpoint is not None
            else HPAI(ip_addr=xknx.multicast_group, port=xknx.multicast_port)
        )

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.discovery_endpoint.from_knx(raw)
        return pos

    def to_knx(self) -> list[int]:
        """Serialize to KNX/IP raw data."""
        data = []
        data.extend(self.discovery_endpoint.to_knx())
        return data

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<SearchRequest discovery_endpoint="{self.discovery_endpoint}" />'
