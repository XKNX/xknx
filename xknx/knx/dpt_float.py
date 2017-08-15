"""Implementation of Basic KNX Floats."""

from xknx.exceptions import ConversionError
from .dpt import DPTBase


class DPTFloat(DPTBase):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.xxx
    """

    value_min = -671088.64
    value_max = 670760.96
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 2)
        data = (raw[0] * 256) + raw[1]
        exponent = (data >> 11) & 0x0f
        significand = data & 0x7ff
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        value = float(significand << exponent) / 100

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
        sign = 1 if value < 0 else 0

        def calc_exponent(value, sign):
            """Return float exponent."""
            exponent = 0
            significand = abs(int(value * 100))

            while significand < -2048 or significand > 2048:
                exponent += 1
                significand >>= 1

            if sign:
                significand ^= 0x7ff  # invert
                significand += 1     # and add 1

            return exponent, significand

        exponent, significand = calc_exponent(value, sign)

        return (sign << 7) | (exponent << 3) | (significand >> 8), \
            significand & 0xff

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return value >= cls.value_min and \
            value <= cls.value_max


class DPTTemperature(DPTFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.001
    """

    value_min = -273
    value_max = 670760
    unit = "C"
    resolution = 1


class DPTLux(DPTFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.004
    """

    value_min = 0
    value_max = 670760
    unit = "Lux"
    resolution = 1


class DPTWsp(DPTFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.005
    """

    value_min = 0
    value_max = 670760
    unit = "m/s"
    resolution = 1


class DPTHumidity(DPTFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.007
    """

    value_min = 0
    value_max = 670760
    unit = "%"
    resolution = 1
