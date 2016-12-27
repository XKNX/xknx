
""" Implementation of Basic KNX Floats """

""" See: http://www.knx.org/fileadmin/template/documents/downloads_support_menu/KNX_tutor_seminar_page/Advanced_documentation/05_Interworking_E1209.pdf as reference """

from enum import Enum
import time
from .dpt import DPT_Base,ConversionError

class DPT_Float(DPT_Base):
    """ Abstraction for KNX 2 Octet Floating Point Numbers """
    """ DPT 9.xxx """

    value_min = -671088.64
    value_max = 670760.96
    unit = ""
    resolution = 1

    @classmethod
    def from_knx(cls, raw):
        """Convert a 2 byte KNX float to a flaot value"""
        cls.test_bytesarray(raw,2)

        data = (raw[0] * 256 ) + raw[1]
        exponent = (data >> 11) & 0x0f
        significand = data & 0x7ff
        sign = data >> 15

        if sign == 1:
            significand = significand - 2048

        value =  float(significand << exponent) / 100

        if not cls.test_boundaries(value):
            raise ConversionError(value)

        return value

    @classmethod
    def to_knx(cls, value):
        """Convert a float to a 2 byte KNX float value"""

        if not isinstance(value, (int, float)):
            raise ConversionError(value)

        if not cls.test_boundaries(value):
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

    @classmethod
    def test_boundaries(cls, value):
        return value >= cls.value_min and \
               value <= cls.value_max

class DPT_Temperature(DPT_Float):
    """ Abstraction for KNX 2 Octet Floating Point Numbers """
    """ DPT 9.001 """

    value_min = -273
    value_max = 670760
    unit = "C"
    resolution = 1

class DPT_Lux(DPT_Float):
    """ Abstraction for KNX 2 Octet Floating Point Numbers """
    """ DPT 9.004 """

    value_min = 0
    value_max = 670760
    unit = "Lux"
    resolution = 1

class DPT_Humidity(DPT_Float):
    """ Abstraction for KNX 2 Octet Floating Point Numbers """
    """ DPT 9.007 """

    value_min = 0
    value_max = 670760
    unit = "%"
    resolution = 1

