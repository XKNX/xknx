
""" Implementation of Basic KNX 2-Byte """

from .dpt import DPTBase, ConversionError

class DPT2Byte(DPTBase):
    """
    Abstraction for KNX 2 Byte
    DPT 7.xxx
    """

    value_min = 0
    value_max = 65535
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Convert a 2 byte KNX int to a int value"""
        cls.test_bytesarray(raw, 2)

        data = (raw[0] * 256) + raw[1]
        exponent = (data >> 11) & 0x0f
        significand = data & 0x7ff
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        value = int(significand << exponent)

        if not cls.test_boundaries(value):
            raise ConversionError(value)

        return value

    @classmethod
    def to_knx(cls, value):
        """Convert a int to a 2 byte KNX value"""

        if not cls.test_boundaries(value):
            raise ConversionError(value)

        sign = 1 if value < 0 else 0

        def calc_exponent(value, sign):
            exponent = 0
            significand = abs(int(value))

            while significand < -2048 or significand > 2048:
                exponent += 1
                significand >>= 1

            if sign:
                significand ^= 0x7ff # invert
                significand += 1     # and add 1

            return exponent, significand

        exponent, significand = calc_exponent(value, sign)

        return (sign << 7) | (exponent << 3) | (significand >> 8), \
               significand & 0xff

    @classmethod
    def test_boundaries(cls, value):
        return value >= cls.value_min and \
               value <= cls.value_max


class DPTCurrent(DPT2Byte):
    """
    Abstraction for KNX 2 Byte
    DPT 7.012
    """

    value_min = 0
    value_max = 65535
    unit = "mA"
    resolution = 1
