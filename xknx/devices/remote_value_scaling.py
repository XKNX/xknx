"""
Module for managing a Scaling remote value.

DPT 5.001.
"""
from xknx.knx import DPTArray, DPTScaling

from .remote_value import RemoteValue


class RemoteValueScaling(RemoteValue):
    """Abstraction for remote value of KNX DPT 5.001 (DPT_Scaling)."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 5.001 (DPT_Scaling)."""
        # pylint: disable=too-many-arguments
        super(RemoteValueScaling, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        if not self.invert:
            value = 100 - value
        return DPTArray(DPTScaling.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        value = DPTScaling.from_knx(payload.value)
        if not self.invert:
            value = 100 - value
        return value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"
