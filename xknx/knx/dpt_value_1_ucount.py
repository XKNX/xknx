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
    payload_length = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)

        value = raw[0]

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse %s" % cls.__name__, value=value, raw=raw)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return (knx_value,)
        except ValueError:
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTPercentU8(DPTValue1Ucount):
    """
    Abstraction for KNX 1 Octet Percent.

    DPT 5.004
    """

    unit = "%"


class DPTSceneNumber(DPTValue1Ucount):
    """
    Abstraction for KNX 1 Octet Scene Number.

    DPT 17.001
    """

    value_min = 1
    value_max = 64

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)

        value = raw[0] + 1

        if not cls._test_boundaries(value):
            raise ConversionError("Cant parse %s" % cls.__name__, value=value, raw=raw)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value) - 1
            if not cls._test_boundaries(knx_value + 1):
                raise ValueError
            return (knx_value,)
        except ValueError:
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)


class DPTTariff(DPTValue1Ucount):
    """
    Abstraction for KNX 1 Octet tariff information.

    DPT 5.006
    """

    value_max = 254
