"""Implementation of Basic KNX 2-Byte."""

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTSignedRelativeValue(DPTBase):
    """
    Abstraction for KNX 1 Byte "1-octet Signed Relative Value".

    DPT 6.010 and 6.001
    """

    value_min = -128
    value_max = 127
    unit = "counter pulses"

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)
        if raw[0] > cls.value_max:
            return raw[0] - 0x100
        return raw[0]

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not cls._test_boundaries(value):
            raise ConversionError("Cant serialize DPTSignedRelativeValue", value=value)
        if value < 0:
            value += 0x100
        return (value & 0xff,)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTPercentV8(DPTSignedRelativeValue):
    """Abstraction for KNX DPT_Percent_V8.

    DPT 6.001
    """

    unit = "%"


class DPTValue1Count(DPTSignedRelativeValue):
    """Abstraction for KNX DPT_Value_1_Count.

    DPT 6.010
    """

    unit = "counter pulses"
