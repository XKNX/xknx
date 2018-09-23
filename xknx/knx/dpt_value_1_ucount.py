"""Implementation of Basic KNX DPT_1_Ucount Values."""
from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTValue1Ucount(DPTBase):
    """
    Abstraction for KNX 1 Octet.

    DPT 5.010
    """

    value_min = 0
    value_max = 255
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)

        value = raw[0]

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse DPTValue1Ucount", value=value, raw=raw)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, (int)):
            raise ConversionError("Cant serialize DPTValue1Ucount", value=value)
        if not cls._test_boundaries(value):
            raise ConversionError("Cant serialize DPTValue1Ucount", value=value)
        return (value,)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max
