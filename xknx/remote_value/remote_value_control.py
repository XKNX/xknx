"""
Module for managing an DPT Control Dimming and Blinds remote value.

DPT 3.007, 3.008
"""
from enum import Enum

from xknx.dpt import DPTControl, DPTControlBlinds, DPTControlDimming
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueControl(RemoteValue):
    """Abstraction for different control DPT types."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        # pylint: disable=invalid-name
        UP = 0
        DOWN = 1
        DECREASE = 0
        INCREASE = 1

    DPTMAP = {
        'control_dimming': DPTControlDimming,
        'control_blinds': DPTControlBlinds
    }

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 sync_state=True,
                 value_type=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize RemoteValueControl class of KNX DPT 3.00x."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address,
                         group_address_state,
                         sync_state=sync_state,
                         device_name=device_name,
                         after_update_cb=after_update_cb)
        self.invert = invert
        if value_type not in self.DPTMAP:
            raise ConversionError("invalid value type", value_type=value_type, device_name=device_name)
        self.value_type = value_type

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTControl)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTControl(self.DPTMAP[self.value_type].to_knx(value, self.invert))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self.DPTMAP[self.value_type].from_knx(payload.value, self.invert)

    async def down(self, step_code=1):
        """Set value to DOWN with default step with 1."""
        value = {
            'control': self.Direction.DOWN.value,
            'step_code': step_code
        }
        await self.set(value)  # (calls to_knx() of this derived class)

    # pylint: disable=invalid-name
    async def up(self, step_code=1):
        """Set value to UP with default step with 1."""
        value = {
            'control': self.Direction.UP.value,
            'step_code': step_code
        }
        await self.set(value)

    async def increase(self, step_code=1):
        """Set value to INCREASE with default step with 1."""
        value = {
            'control': self.Direction.INCREASE.value,
            'step_code': step_code
        }
        await self.set(value)

    async def decrease(self, step_code=1):
        """Set value to DECREASE with default step with 1."""
        value = {
            'control': self.Direction.DECREASE.value,
            'step_code': step_code
        }
        await self.set(value)

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
