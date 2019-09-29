"""
Implementation of Basic KNX 2-Byte Signed Values.

They correspond the following KNX DPTs:
    8.*** 2-byte/octet signed (2's complement), i.e. percentV16, delta time
"""

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT2ByteSigned(DPTBase):
    """
    Abstraction for KNX 2 Byte signed values.

    DPT 8.***
    """

    value_min = -32768
    value_max = 32767
    unit = ""
    resolution = 1
    payload_length = 2

    _struct_format = ">h"

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 2)

        try:
            return struct.unpack(cls._struct_format, bytes(raw))[0]
        except struct.error:
            raise ConversionError("Cant parse %s" % cls.__name__, raw=raw)

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return tuple(struct.pack(cls._struct_format, knx_value))
        except (ValueError, struct.error):
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value):
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTValue2Count(DPT2ByteSigned):
    """DPT 8.001 DPT_Value_2_Count (pulses)."""

    unit = "pulses"


class DPTDeltaTimeMsec(DPT2ByteSigned):
    """DPT 8.002 DPT_DeltaTimeMsec (ms)."""

    unit = "ms"


class DPTDeltaTimeSec(DPT2ByteSigned):
    """DPT 8.005 DPT_DeltaTimeSec (s)."""

    unit = "s"


class DPTDeltaTimeMin(DPT2ByteSigned):
    """DPT 8.006 DPT_DeltaTimeMin (min)."""

    unit = "min"


class DPTDeltaTimeHrs(DPT2ByteSigned):
    """DPT 8.007 DPT_DeltaTimeHrs (h)."""

    unit = "h"


class DPTPercentV16(DPT2ByteSigned):
    """DPT 8.010 DPT_Percent_V16 (%)."""

    unit = "%"
    resolution = 0.01


class DPTRotationAngle(DPT2ByteSigned):
    """DPT 8.011 DPT_Rotation_Angle (°)."""

    unit = "°"
