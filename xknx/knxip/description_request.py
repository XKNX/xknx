"""
Module for Serialization and Deserialization of KNX Description Requests.

The DESCRIPTION_REQUEST frame shall be sent by the KNXnet/IP Client to the control endpoint
of the KNXnet/IP Server to obtain a self-description of the KNXnet/IP Server device.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .body import KNXIPBody
from .hpai import HPAI
from .knxip_enum import KNXIPServiceType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class DescriptionRequest(KNXIPBody):
    """Representation of a KNX Descriptoin Request."""

    SERVICE_TYPE = KNXIPServiceType.DESCRIPTION_REQUEST

    def __init__(self, xknx: XKNX, control_endpoint: HPAI = HPAI()):
        """Initialize SearchRequest object."""
        super().__init__(xknx)
        self.control_endpoint = control_endpoint

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return HPAI.LENGTH

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        return self.control_endpoint.from_knx(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        return self.control_endpoint.to_knx()

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<DescriptionRequest control_endpoint="{self.control_endpoint}" />'
