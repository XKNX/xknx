"""Implementation of Basic KNX DPT_Scaling (Percent) Values."""
from xknx.exceptions import ConversionError
from .dpt import DPTBase


class DPTScaling(DPTBase):
    """
    Abstraction for KNX 1 Octet DPT_Scaling.

    DPT 5.001
    """

    value_min = 0
    value_max = 100
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)

        value = round((raw[0]/256)*100)

        if not cls._test_boundaries(value):
            raise ConversionError(value)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, (int, float)):
            raise ConversionError(value)
        if not cls._test_boundaries(value):
            raise ConversionError(value)
        knx_value = round(value/100*255.4)
        return (knx_value,)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return value >= cls.value_min and \
            value <= cls.value_max
