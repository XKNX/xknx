"""Implementation of Basic KNX 1-Byte signed integer values."""

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTSignedRelativeValue(DPTBase):
    """
    Abstraction for KNX 1 Byte "1-octet Signed Relative Value".

    DPT 6.***
    """

    value_min = -128
    value_max = 127
    unit = ""
    payload_length = 1

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
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            if knx_value < 0:
                knx_value += 0x100
            return (knx_value & 0xff,)
        except ValueError:
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

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
