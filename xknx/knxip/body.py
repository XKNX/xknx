"""Basis class for all KNX/IP bodies."""


class KNXIPBody():
    """Basis class for all KNX/IP bodies."""

    def __init__(self, xknx):
        """Initialize KNXIPBody object."""
        self.xknx = xknx

    def calculated_length(self):
        """Get length of KNX/IP body."""
        pass

    def from_knx(self, raw):
        """Parse/deserialize from KNX/IP raw data."""
        pass

    def to_knx(self):
        """Serialize to KNX/IP raw data."""
        pass
