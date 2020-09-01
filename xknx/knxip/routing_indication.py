"""
Module for Serialization and Deserialization of KNX Routing Indications.

Routing indications are used to transport CEMI Messages.
"""
from xknx.exceptions import UnsupportedCEMIMessage

from .body import KNXIPBody
from .cemi_frame import CEMIFrame
from .knxip_enum import KNXIPServiceType


class RoutingIndication(KNXIPBody):
    """Representation of a KNX Routing Indication."""

    # pylint: disable=too-many-instance-attributes

    service_type = KNXIPServiceType.ROUTING_INDICATION

    def __init__(self, xknx):
        """Initialize SearchRequest object."""
        super().__init__(xknx)
        self.cemi = CEMIFrame(xknx)

    def calculated_length(self):
        """Get length of KNX/IP body."""
        return self.cemi.calculated_length()

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        try:
            return self.cemi.from_knx(raw)
        except UnsupportedCEMIMessage as unsupported_cemi_err:
            self.xknx.logger.warning("CEMI not supported: %s", unsupported_cemi_err)
            self.cemi = None
            return len(raw)

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        return self.cemi.to_knx()

    def __str__(self):
        """Return object as readable string."""
        return f'<RoutingIndication cemi="{self.cemi}" />'
