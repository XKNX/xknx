"""
Module for managing an DPT Step remote value.

DPT 1.007.
"""
from enum import Enum

from xknx.dpt import DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import RemoteValue


class RemoteValueStep(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.007 / DPT_Step."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        DECREASE = 0
        INCREASE = 1

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 1.007."""
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

    # from KNX Association System Specifications AS v1.5.00:
    # 1.007 DPT_Step   0 = Decrease 1 = Increase
    # 1.008 DPT_UpDown 0 = Up       1 = Down

    def to_knx(self, value):
        """Convert value to payload."""
        if value == self.Direction.INCREASE:
            return DPTBinary(0) if self.invert else DPTBinary(1)
        if value == self.Direction.DECREASE:
            return DPTBinary(1) if self.invert else DPTBinary(0)
        raise ConversionError("value invalid", value=value, device_name=self.device_name)

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.Direction.DECREASE if self.invert else self.Direction.INCREASE
        if payload == DPTBinary(0):
            return self.Direction.INCREASE if self.invert else self.Direction.DECREASE
        raise CouldNotParseTelegram("payload invalid", payload=payload, device_name=self.device_name)

    async def increase(self):
        """Increase value."""
        await self.set(self.Direction.INCREASE)

    async def decrease(self):
        """Decrease the value."""
        await self.set(self.Direction.DECREASE)
