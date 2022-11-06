"""
Module for Serialization and Deserialization of KNX Extended Search Requests.

Extended Search Requests are used to search for KNX/IP devices within the network that support for instance IP Secure.

See AN184 in version 03 from the KNX specifications.
"""
from __future__ import annotations

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType
from .srp import SRP


class SearchRequestExtended(KNXIPBody):
    """Representation of a KNX Search Request Extended."""

    SERVICE_TYPE = KNXIPServiceType.SEARCH_REQUEST_EXTENDED

    def __init__(
        self,
        discovery_endpoint: HPAI | None = None,
        srps: list[SRP] | None = None,
    ):
        """Initialize SearchRequestExtended object."""
        self.discovery_endpoint = discovery_endpoint or HPAI()
        self.srps = srps or []

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH + sum(srp.payload_size for srp in self.srps)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        pos: int = self.discovery_endpoint.from_knx(raw)
        while raw[pos:]:
            srp = SRP.from_knx(raw[pos:])
            pos += len(srp)
            self.srps.append(srp)

        return pos

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.discovery_endpoint.to_knx() + b"".join(
            bytes(srp) for srp in self.srps
        )

    def __repr__(self) -> str:
        """Return object as readable string."""
        return (
            "<SearchRequestExtended "
            f'discovery_endpoint="{self.discovery_endpoint}" '
            f'srps="{self.srps}" />'
        )
