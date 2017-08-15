"""Implementation of Basic KNX 2-Byte."""

from xknx.exceptions import ConversionError
from .dpt import DPTBase


class DPT2Byte(DPTBase):
    """
    Abstraction for KNX 2 Byte "2-octet unsigned counter value".

    DPT 7.001
    """

    value_min = 0
    value_max = 65535
    unit = "pulses"
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 2)
        return (raw[0] * 256) + raw[1]

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not cls._test_boundaries(value):
            raise ConversionError(value)
        return value >> 8, value & 0xff

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return value >= cls.value_min and \
            value <= cls.value_max


class DPTUElCurrentmA(DPT2Byte):
    """
    Abstraction for KNX 2 Byte DPTUElCurrentmA.

    DPT 7.012
    """

    value_min = 0
    value_max = 65535
    unit = "mA"
    resolution = 1
