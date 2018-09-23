"""
Module for managing an DPT Switch remote value.

DPT 1.001.
"""
from enum import Enum

from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.knx import DPTBinary

from .remote_value import RemoteValue


class RemoteValueSwitch(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.001 / DPT_Switch."""

    class Value(Enum):
        """Enum for indicating the direction."""

        # pylint: disable=invalid-name
        OFF = 0
        ON = 1

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 1.001."""
        # pylint: disable=too-many-arguments
        super(RemoteValueSwitch, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        if value == self.Value.OFF:
            return DPTBinary(1) if self.invert else DPTBinary(0)
        if value == self.Value.ON:
            return DPTBinary(0) if self.invert else DPTBinary(1)
        raise ConversionError("value invalid", value=value, device_name=self.device_name)

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload == DPTBinary(0):
            return self.Value.ON if self.invert else self.Value.OFF
        if payload == DPTBinary(1):
            return self.Value.OFF if self.invert else self.Value.ON
        raise CouldNotParseTelegram("payload invalid", payload=payload, device_name=self.device_name)

    async def off(self):
        """Set value to down."""
        await self.set(self.Value.OFF)

    async def on(self):
        """Set value to UP."""
        # pylint: disable=invalid-name
        await self.set(self.Value.ON)
