"""Implementation of Basic KNX 2-Byte/octet values."""

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT2ByteUnsigned(DPTBase):
    """
    Abstraction for KNX 2 Byte "2-octet unsigned value".

    Contains smaller counters, timers  etc.

    DPT 7.xxx
    """

    value_min = 0
    value_max = 65535
    unit = ""
    resolution = 1
    payload_length = 2

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 2)
        return (raw[0] * 256) + raw[1]

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not cls._test_boundaries(value):
            raise ConversionError("Cant serialize DPT2ByteUnsigned", value=value)
        return value >> 8, value & 0xff

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPT2Ucount(DPT2ByteUnsigned):
    """DPT 7.001 DPT_Value_2_Ucount."""

    unit = "pulses"


class DPTUElCurrentmA(DPT2ByteUnsigned):
    """DPT 7.012 Abstraction for KNX 2 Byte DPTUElCurrentmA."""

    unit = "mA"


class DPTBrightness(DPT2ByteUnsigned):
    """DPT 7.012 DPT_Brightness (lux)."""

    unit = "lx"
