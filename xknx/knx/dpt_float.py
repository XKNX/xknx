"""
Implementation of KNX Float-values.

They can be either 2 or 4 bytes, and correspond to the the following KDN DPTs.
    9.yyy  2-byte/octet float, e.g. temperature
    14.yyy 4-byte/octet float, IEEE 754, i.e. Electrical measurements: current, power
"""

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT2ByteFloat(DPTBase):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.xxx
    """

    value_min = -671088.64
    value_max = 670760.96
    unit = ""
    resolution = 1
    payload_length = 2

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
            raise ConversionError("Cant parse DPT2ByteFloat", value=value)

        return value

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, (int, float)):
            raise ConversionError("Cant serialize DPT2ByteFloat", value=value, type=type(value))
        if not cls._test_boundaries(value):
            raise ConversionError("Cant serialize DPT2ByteFloat", value=value)
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
        return cls.value_min <= value <= cls.value_max


class DPT4ByteFloat(DPTBase):
    """
    Abstraction for KNX 4 Octet Floating Point Numbers, with a maximum usable range as specified in IEEE 754.

    The largest positive finite float literal is 3.40282347e+38f.
    The smallest positive finite non-zero literal of type float is 1.40239846e-45f.
    The negative minimum finite float literal is -3.40282347e+38f.
    No value range are defined for DPTs 14.000-079.

    DPT 14.xxx
    """

    unit = ""
    payload_length = 4

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data (big endian)."""
        cls.test_bytesarray(raw, 4)
        try:
            return struct.unpack(">f", bytes(raw))[0]
        except struct.error:
            raise ConversionError("Cant parse DPT4ByteFloat", raw=raw)

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            return tuple(struct.pack(">f", value))
        except struct.error:
            raise ConversionError("Cant serialize DPT4ByteFloat", vlaue=value)


class DPTTemperature(DPT2ByteFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.001 DPT_Value_Temp
    """

    value_min = -273
    value_max = 670760
    unit = "°C"
    resolution = 1


class DPTLux(DPT2ByteFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.004 DPT_Value_Lux
    """

    value_min = 0
    value_max = 670760
    unit = "lx"
    resolution = 1


class DPTWsp(DPT2ByteFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.005 DPT_Value_Ws Speed (m/s)
    """

    value_min = 0
    value_max = 670760
    unit = "m/s"
    resolution = 1


class DPTHumidity(DPT2ByteFloat):
    """
    Abstraction for KNX 2 Octet Floating Point Numbers.

    DPT 9.007 DPT_Value_Humidity.
    """

    value_min = 0
    value_max = 670760
    unit = "%"
    resolution = 1


class DPTElectricCurrent(DPT4ByteFloat):
    """DPT 14.019 DPT_Value_Electric_Current."""

    unit = "A"


class DPTElectricPotential(DPT4ByteFloat):
    """DPT 14.027 DPT_Value_Electric_Potential."""

    unit = "V"


class DPTEnergy(DPT4ByteFloat):
    """DPT 14.031 DPT_Value_Energy."""

    unit = 'J'


class DPTFrequency(DPT4ByteFloat):
    """DPT 14.033 DPT_Value_Frequency."""

    unit = 'Hz'


class DPTHeatFlowRate(DPT4ByteFloat):
    """DPT 14.036 DPT_Value_Heat_Flow_Rate."""

    unit = 'W'


class DPTPhaseAngleRad(DPT4ByteFloat):
    """DPT 14.054 DPT_Value_Phase_Angle, Radiant."""

    unit = 'rad'


class DPTPhaseAngleDeg(DPT4ByteFloat):
    """14.055 DPT_Value_Phase_Angle, Degree."""

    unit = '°'


class DPTPower(DPT4ByteFloat):
    """DPT 14.056 DPT_Value_Power."""

    unit = "W"


class DPTPowerFactor(DPT4ByteFloat):
    """DPT 14.057 DPT_Value_Power."""

    unit = ''


class DPTSpeed(DPT4ByteFloat):
    """DPT 14.065 DPT_Value_Speed."""

    unit = 'm/s'
