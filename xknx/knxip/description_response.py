"""
Module for Serialization and Deserialization of KNX Description Response.

The DESCRIPTION_RESPONSE frame shall be sent by the KNXnet/IP Server as an answer to
a received DESCRIPTION_REQUEST frame. It shall be addressed to the KNXnet/IP Clients
control endpoint using the HPAI included in the received DESCRIPTION_REQUEST frame.
The size of the KNXnet/IP body varies depending on the number of DIB structures sent
by the KNXnet/IP Server in response to the KNXnet/IP Clients DESCRIPTION_REQUEST.
"""
from __future__ import annotations

from .body import KNXIPBody
from .dib import DIB, DIBDeviceInformation
from .knxip_enum import KNXIPServiceType


class DescriptionResponse(KNXIPBody):
    """Representation of a KNX Description Response."""

    SERVICE_TYPE = KNXIPServiceType.DESCRIPTION_RESPONSE

    def __init__(self) -> None:
        """Initialize SearchResponse object."""
        self.dibs: list[DIB] = []

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        return sum(dib.calculated_length() for dib in self.dibs)

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        pos = 0
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
        return b"".join(dib.to_knx() for dib in self.dibs)

    def __repr__(self) -> str:
        """Return object as readable string."""
        _dibs_str = ",\n".join(dib.__repr__() for dib in self.dibs)
        return "<DescriptionResponse " f'dibs="[\n{_dibs_str}\n]" />'
