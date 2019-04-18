"""Implementation of scaled KNX DPT_1_Ucount Values."""
from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTScaling(DPTBase):
    """
    Abstraction for KNX 1 Octet Percent.

    DPT 5.001
    """

    value_min = 0
    value_max = 100
    resolution = 100/255
    unit = "%"
    payload_length = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)

        knx_value = raw[0]
        delta = cls.value_max - cls.value_min
        value = round((knx_value/255)*delta) + cls.value_min

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse %s" % cls.__name__, value=value, raw=raw)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            percent_value = float(value)
            if not cls._test_boundaries(percent_value):
                raise ValueError
            delta = cls.value_max - cls.value_min
            knx_value = round((percent_value-cls.value_min)/delta*255)

            return (knx_value,)
        except ValueError:
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTAngle(DPTScaling):
    """
    Abstraction for KNX 1 Octet Angle.

    DPT 5.003
    """

    value_min = 0
    value_max = 360
    resolution = 360/255
    unit = "°"
