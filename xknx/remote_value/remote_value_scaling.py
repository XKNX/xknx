"""
Module for managing a Scaling remote value.

DPT 5.001.
"""
from xknx.dpt import DPTArray

from .remote_value import RemoteValue


class RemoteValueScaling(RemoteValue):
    """Abstraction for remote value of KNX DPT 5.001 (DPT_Scaling)."""

    def __init__(self,
                 xknx,
                 *a,
                 range_from=0,
                 range_to=100,
                 **kw):
        """Initialize remote value of KNX DPT 5.001 (DPT_Scaling)."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, *a, **kw)
        self.range_from = range_from
        self.range_to = range_to

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        knx_value = self._calc_to_knx(self.range_from, self.range_to, value)
        return DPTArray(knx_value)

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self._calc_from_knx(self.range_from, self.range_to, payload.value[0])

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"

    @staticmethod
    def _calc_from_knx(range_from, range_to, raw):
        delta = range_to - range_from
        return round((raw/255)*delta) + range_from

    @staticmethod
    def _calc_to_knx(range_from, range_to, value):
        delta = range_to - range_from
        return round((value-range_from)/delta*255)
