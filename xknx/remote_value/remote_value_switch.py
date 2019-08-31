"""
Module for managing an DPT Switch remote value.

DPT 1.001.
"""
from xknx.dpt import DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueSwitch(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.001 / DPT_Switch."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 1.001."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address,
                         group_address_state,
                         device_name=device_name,
                         after_update_cb=after_update_cb)
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        if isinstance(value, bool):
            return DPTBinary(value ^ self.invert)
        raise ConversionError("value invalid", value=value, device_name=self.device_name)

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload == DPTBinary(0):
            return self.invert
        if payload == DPTBinary(1):
            return not self.invert
        raise CouldNotParseTelegram("payload invalid", payload=payload, device_name=self.device_name)

    async def off(self):
        """Set value to down."""
        await self.set(False)

    async def on(self):
        """Set value to UP."""
        # pylint: disable=invalid-name
        await self.set(True)
