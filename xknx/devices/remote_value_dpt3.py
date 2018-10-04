"""
Module for managing an DPT Control Dimming/Blinds remote value.

DPT 3.007/3.008.

Very good source of information for interpretation of the standard is
https://library.e.abb.com/public/78c74aa86d4648b7b9d918485cd4621a/2CDC500051M0203_ApplicationHB_Lighting_EN.pdf#page=34

There are two separate dimming modes sharing the same DPT class:

 * Stepwise dimming
   The full brightness range is divided into 2^(stepcode-1) intervals.
   The value is always rounded to full interval boundary, i.e. 30% +25% = 50%, 50% +25% = 75%, 30% -25% = 25%

 * Start-stop dimming
   Dimming is started with -/+100% (0x1/0x9) and keeps dimming until a STOP diagram (0x0/0x8) is received.
"""
from enum import Enum

from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.knx import DPTBinary

from .remote_value import RemoteValue


class RemoteValueDpt3(RemoteValue):
    """Abstraction for remote value of KNX DPT 3.007 / DPT_Control_Dimming or DPT 3.008 / DPT_Control_Blinds."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 3.007/3.008."""
        # pylint: disable=too-many-arguments
        super(RemoteValueDpt3, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        sign = 0 if value < 0 else 1
        if self.invert: sign = 1 if sign==0 else 0

        if   abs(value)>=100: return DPTBinary(sign<<3 | 1)
        elif abs(value)>=50:  return DPTBinary(sign<<3 | 2)
        elif abs(value)>=25:  return DPTBinary(sign<<3 | 3)
        elif abs(value)>=12:  return DPTBinary(sign<<3 | 4)
        elif abs(value)>=6:   return DPTBinary(sign<<3 | 5)
        elif abs(value)>=3:   return DPTBinary(sign<<3 | 6)
        elif abs(value)>=1:   return DPTBinary(sign<<3 | 7)
        else:                 return DPTBinary(          0)

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload.value & ~0x0F != 0: # more than 4-bit
            raise CouldNotParseTelegram("payload invalid", payload=payload, device_name=self.device_name)
        # calculated using floor(100/2^((value&0x07)-1))
        value = [0,-100,-50,-25,-12,-6,-3,-1,0,100,50,25,12,6,3,1][payload.value & 0x0F]
        return value if not self.invert else -value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "%"


class RemoteValueStartStopDimming(RemoteValue):
    """Abstraction for remote value of KNX DPT 3.007 / DPT_Control_Dimming."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        DECREASE = 0
        INCREASE = 1
        STOP = 2

        def __str__(self):
            return self.name

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 3.007."""
        # pylint: disable=too-many-arguments
        super(RemoteValueStartStopDimming, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        if value == self.Direction.INCREASE:
            return DPTBinary(0x09) if not self.invert else DPTBinary(0x01)
        elif value == self.Direction.DECREASE:
            return DPTBinary(0x01) if not self.invert else DPTBinary(0x09)
        elif value == self.Direction.STOP:
            return DPTBinary(0x00)
        raise ConversionError("value invalid", value=value, device_name=self.device_name)

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload.value & ~0x0F != 0: # more than 4-bit
            pass # raises exception below
        elif payload.value & 0x07 == 0:
            return self.Direction.STOP
        elif payload.value & 0x08 == 0:
            return self.Direction.DECREASE if not self.invert else self.Direction.INCREASE
        else:
            return self.Direction.INCREASE if not self.invert else self.Direction.DECREASE
        raise CouldNotParseTelegram("payload invalid", payload=payload, device_name=self.device_name)

    async def increase(self):
        """Increase value."""
        await self.set(self.Direction.INCREASE)

    async def decrease(self):
        """Decrease the value."""
        await self.set(self.Direction.DECREASE)

    async def stop(self):
        """Don't change value."""
        await self.set(self.Direction.STOP)


class RemoteValueStartStopBlinds(RemoteValue):
    """Abstraction for remote value of KNX DPT 3.008 / DPT_Control_Blinds."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        UP = 0
        DOWN = 1
        STOP = 2

        def __str__(self):
            return self.name

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 invert=False):
        """Initialize remote value of KNX DPT 3.008."""
        # pylint: disable=too-many-arguments
        super(RemoteValueStartStopBlinds, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)
        self.invert = invert

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        if value == self.Direction.DOWN:
            return DPTBinary(0x09) if not self.invert else DPTBinary(0x01)
        elif value == self.Direction.UP:
            return DPTBinary(0x01) if not self.invert else DPTBinary(0x09)
        elif value == self.Direction.STOP:
            return DPTBinary(0x00)
        raise ConversionError("value invalid", value=value, device_name=self.device_name)

    def from_knx(self, payload):
        """Convert current payload to value."""
        if payload.value & ~0x0F != 0: # more than 4-bit
            pass # raises exception below
        elif payload.value & 0x07 == 0:
            return self.Direction.STOP
        elif payload.value & 0x08 == 0:
            return self.Direction.UP if not self.invert else self.Direction.DOWN
        else:
            return self.Direction.DOWN if not self.invert else self.Direction.UP
        raise CouldNotParseTelegram("payload invalid", payload=payload, device_name=self.device_name)

    async def up(self):
        """Set value to up."""
        await self.set(self.Direction.UP)

    async def down(self):
        """Set value to down."""
        await self.set(self.Direction.DOWN)

    async def stop(self):
        """Don't change value."""
        await self.set(self.Direction.STOP)
