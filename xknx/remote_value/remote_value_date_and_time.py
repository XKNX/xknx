"""
Module for managing DPT with date and time values.

DPT 10.001, 11.001, 19.002
"""
from xknx.dpt import DPTArray, DPTDate, DPTDateTime, DPTTime
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueDateAndTime(RemoteValue):
    """Abstraction for different date and time DPT types."""

    DPTMAP = {
        'date': DPTDate,
        'time': DPTTime,
        'timeofday': DPTDateTime
    }

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 sync_state=True,
                 value_type=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize RemoteValueControl class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address,
                         group_address_state,
                         sync_state=sync_state,
                         device_name=device_name,
                         after_update_cb=after_update_cb)
        if value_type not in self.DPTMAP:
            raise ConversionError("invalid value type", value_type=value_type, device_name=device_name)
        self.value_type = value_type

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        number_bytes = 8 if (self.value_type == 'timeofday') else 3
        return (isinstance(payload, DPTArray)
                and len(payload.value) == number_bytes)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(self.DPTMAP[self.value_type].to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self.DPTMAP[self.value_type].from_knx(payload.value)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.DPTMAP[self.value_type].unit

    @property
    def ha_device_class(self):
        """Return a string representing the home assistant device class."""
        if hasattr(self.DPTMAP[self.value_type], 'ha_device_class'):
            return self.DPTMAP[self.value_type].ha_device_class
        return None
