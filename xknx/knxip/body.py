"""Basis class for all KNX/IP bodies."""
import logging

logger = logging.getLogger("xknx.log")


class KNXIPBody:
    """Basis class for all KNX/IP bodies."""

    def __init__(self, xknx):
        """Initialize KNXIPBody object."""
        self.xknx = xknx

    def calculated_length(self):
        """Get length of KNX/IP body."""
        logger.warning(
            "'calculated_length()' not implemented for %s", self.__class__.__name__
        )

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        # pylint: disable=unused-argument
        logger.warning("'from_knx()' not implemented for %s", self.__class__.__name__)

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        logger.warning("'to_knx()' not implemented for %s", self.__class__.__name__)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
