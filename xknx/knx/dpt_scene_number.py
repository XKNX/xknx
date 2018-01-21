"""Implementation of Basic KNX DPT_Scaling (Percent) Values."""
from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTSceneNumber(DPTBase):
    """
    Abstraction for KNX 1 Octet Scene Number.

    DPT 17.001
    """

    value_min = 0
    value_max = 63
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)

        value = raw[0]

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse DPTSceneNumber", value=value, raw=raw)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, (int)):
            raise ConversionError("Cant serialize DPTSceneNumber", value=value)
        if not cls._test_boundaries(value):
            raise ConversionError("Cant serialize DPTSceneNumber", value=value)
        return (value,)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return value >= cls.value_min and \
            value <= cls.value_max
