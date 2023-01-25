"""
Module for Serialization and Deserialization of KNX Search Response.

Search Requests are used to search for KNX/IP devices within the network.
A search response contains all information of a found device (Name, serial number, supported features.).
It supports an array-style access to the DIBs (use classname as index). Every KNXnet/ip server shall send
a search response and one device supporting multiple KNX connections may send multiple search responses.
"""
from __future__ import annotations

from .body import KNXIPBody
from .dib import DIB, DIBDeviceInformation
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType


class SearchResponse(KNXIPBody):
    """Representation of a KNX Search Response."""

    SERVICE_TYPE = KNXIPServiceType.SEARCH_RESPONSE

    def __init__(self, control_endpoint: HPAI | None = None) -> None:
        """Initialize SearchResponse object."""
        self.control_endpoint = control_endpoint or HPAI()
        self.dibs: list[DIB] = []

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH + sum(dib.calculated_length() for dib in self.dibs)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        pos = self.control_endpoint.from_knx(raw)
        while raw[pos:]:
            dib = DIB.determine_dib(raw[pos:])
            pos += dib.from_knx(raw[pos:])
            self.dibs.append(dib)
        return pos

    @property
    def device_name(self) -> str:
        """Return name of device."""
        return next(
            (dib.name for dib in self.dibs if isinstance(dib, DIBDeviceInformation)),
            "UNKNOWN",
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.control_endpoint.to_knx() + b"".join(
            dib.to_knx() for dib in self.dibs
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        _dibs_str = ",\n".join(dib.__str__() for dib in self.dibs)
        return (
            "<SearchResponse "
            f'control_endpoint="{self.control_endpoint}" '
            f'dibs="[\n{_dibs_str}\n]" />'
        )
