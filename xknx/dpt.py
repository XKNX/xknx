
class ConversionError(Exception):
    def __init__(self, i):
        self.i = i
    def __str__(self):
        return "<ConversionError input='{0}'>".format(self.i)


class DPT_BASE:

    @staticmethod
    def test_bytesarray( raw,length ):
        if type(raw) is not tuple \
                or len(raw) != length \
                or any(not isinstance(byte,int) for byte in raw) \
                or any(byte < 0 for byte in raw) \
                or any(byte > 255 for byte in raw):
            raise ConversionError(raw)

class DPT_Float(DPT_BASE):
    """ Abstraction for KNX 2 Octet Floating Point Numbers """
    """ DPT 9.xxx """

    value_min = -671088.64 
    value_max = 670760.96

    @staticmethod
    def from_knx(raw):
        """Convert a 2 byte KNX float to a flaot value"""
        DPT_BASE.test_bytesarray(raw,2)

        data = (raw[0] * 256 ) + raw[1]
        exponent = (data >> 11) & 0x0f
        significand = data & 0x7ff
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        return float(significand << exponent) / 100


    @staticmethod
    def to_knx(value):
        """Convert a float to a 2 byte KNX float value"""

        if not isinstance(value, (int, float)):
            raise ConversionError(value)

        if value < DPT_Float.value_min or \
                value > DPT_Float.value_max:
            raise ConversionError(value)

        sign = 1 if value < 0 else 0

        def calc_exponent(value, sign):
            exponent = 0
            significand = abs ( int (value * 100) )

            while significand < -2048 or significand > 2048:
                exponent += 1
                significand >>= 1

            if sign:
                significand ^= 0x7ff # invert
                significand += 1     # and add 1

            return exponent,significand

        exponent,significand = calc_exponent(value, sign)

        return (sign << 7) | (exponent << 3) | (significand >> 8), significand & 0xff
