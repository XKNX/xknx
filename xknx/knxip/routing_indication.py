"""
Module for Serialization and Deserialization of KNX Routing Indications.

Routing indications are used to transport CEMI Messages.
"""
from __future__ import annotations

import logging

from xknx.exceptions import CouldNotParseKNXIP, UnsupportedCEMIMessage

from .body import KNXIPBody
from .cemi_frame import CEMIFrame
from .knxip_enum import CEMIMessageCode, KNXIPServiceType

logger = logging.getLogger("xknx.log")


class RoutingIndication(KNXIPBody):
    """Representation of a KNX Routing Indication."""

    SERVICE_TYPE = KNXIPServiceType.ROUTING_INDICATION

    def __init__(self, cemi: CEMIFrame | None = None):
        """Initialize SearchRequest object."""
        self.cemi: CEMIFrame | None = (
            cemi if cemi is not None else CEMIFrame(code=CEMIMessageCode.L_DATA_IND)
        )

    def calculated_length(self) -> int:
        """Get length of KNX/IP body."""
        assert self.cemi is not None
        return self.cemi.calculated_length()

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        assert self.cemi is not None

        try:
            return self.cemi.from_knx(raw)
        except UnsupportedCEMIMessage as unsupported_cemi_err:
            logger.warning("CEMI not supported: %s", unsupported_cemi_err)
            self.cemi = None
            return len(raw)

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        if self.cemi is None:
            raise CouldNotParseKNXIP("No CEMIFrame defined.")
        return self.cemi.to_knx()

    def __repr__(self) -> str:
        """Return object as readable string."""
        return f'<RoutingIndication cemi="{self.cemi}" />'
