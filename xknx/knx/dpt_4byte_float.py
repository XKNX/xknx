"""
Implementation of KNX 4 byte Float-values.

They correspond to the the following KDN DPT 14 class.
"""

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT4ByteFloat(DPTBase):
    """
    Abstraction for KNX 4 Octet Floating Point Numbers, with a maximum usable range as specified in IEEE 754.

    The largest positive finite float literal is 3.40282347e+38f.
    The smallest positive finite non-zero literal of type float is 1.40239846e-45f.
    The negative minimum finite float literal is -3.40282347e+38f.
    No value range are defined for DPTs 14.000-079.

    DPT 14.***
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
            raise ConversionError("Cant parse %s" % cls.__name__, raw=raw)

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = float(value)
            return tuple(struct.pack(">f", knx_value))
        except (ValueError, struct.error):
            raise ConversionError("Cant serialize %s" % cls.__name__, vlaue=value)


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


class DPTLuminousFlux(DPT4ByteFloat):
    """DPT 14.042 DPT_Value_Heat_Flow_Rate."""

    unit = 'lm'
    ha_device_class = "illuminance"


class DPTPhaseAngleRad(DPT4ByteFloat):
    """DPT 14.054 DPT_Value_Phase_Angle, Radiant."""

    unit = 'rad'


class DPTPhaseAngleDeg(DPT4ByteFloat):
    """DPT 14.055 DPT_Value_Phase_Angle, Degree."""

    unit = '°'


class DPTPower(DPT4ByteFloat):
    """DPT 14.056 DPT_Value_Power."""

    unit = "W"
    ha_device_class = "power"


class DPTPowerFactor(DPT4ByteFloat):
    """DPT 14.057 DPT_Value_Power."""

    unit = ''


class DPTPressure(DPT4ByteFloat):
    """DPT 14.058 DPT_Value_Pressure."""

    unit = 'Pa'
    ha_device_class = "pressure"


class DPTSpeed(DPT4ByteFloat):
    """DPT 14.065 DPT_Value_Speed."""

    unit = 'm/s'
