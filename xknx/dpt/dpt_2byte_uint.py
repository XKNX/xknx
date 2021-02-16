"""Implementation of Basic KNX 2-Byte/octet values."""
from typing import Optional, Tuple

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT2ByteUnsigned(DPTBase):
    """
    Abstraction for KNX 2 Byte "2-octet unsigned value".

    Contains smaller counters, timers  etc.

    DPT 7.***
    """

    value_min = 0
    value_max = 65535
    dpt_main_number = 7
    dpt_sub_number: Optional[int] = None
    value_type = "2byte_unsigned"
    unit = ""
    resolution = 1
    payload_length = 2

    @classmethod
    def from_knx(cls, raw: Tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        return (raw[0] * 256) + raw[1]

    @classmethod
    def to_knx(cls, value: int) -> Tuple[int, int]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return knx_value >> 8, knx_value & 0xFF
        except ValueError:
            raise ConversionError("Could not serialize %s" % cls.__name__, value=value)

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPT2Ucount(DPT2ByteUnsigned):
    """DPT 7.001 DPT_Value_2_Ucount."""

    dpt_main_number = 7
    dpt_sub_number = 1
    value_type = "pulse_2byte"
    unit = "pulses"


class DPTTimePeriodMsec(DPT2ByteUnsigned):
    """DPT 7.002 DPT_TimePeriodMsec (ms)."""

    dpt_main_number = 7
    dpt_sub_number = 2
    value_type = "time_period_msec"
    unit = "ms"


class DPTTimePeriod10Msec(DPT2ByteUnsigned):
    """DPT 7.003 DPT_TimePeriod10Msec (ms)."""

    dpt_main_number = 7
    dpt_sub_number = 3
    value_type = "time_period_10msec"
    unit = "ms"
    resolution = 10


class DPTTimePeriod100Msec(DPT2ByteUnsigned):
    """DPT 7.004 DPT_TimePeriod100Msec (ms)."""

    dpt_main_number = 7
    dpt_sub_number = 4
    value_type = "time_period_100msec"
    unit = "ms"
    resolution = 100


class DPTTimePeriodSec(DPT2ByteUnsigned):
    """DPT 7.005 DPT_TimePeriodSec (s)."""

    dpt_main_number = 7
    dpt_sub_number = 5
    value_type = "time_period_sec"
    unit = "s"


class DPTTimePeriodMin(DPT2ByteUnsigned):
    """DPT 7.006 DPT_TimePeriodMin (min)."""

    dpt_main_number = 7
    dpt_sub_number = 6
    value_type = "time_period_min"
    unit = "min"


class DPTTimePeriodHrs(DPT2ByteUnsigned):
    """DPT 7.007 DPT_TimePeriodHrs (h)."""

    dpt_main_number = 7
    dpt_sub_number = 7
    value_type = "time_period_hrs"
    unit = "h"


class DPTLengthMm(DPT2ByteUnsigned):
    """DPT 7.011 Abstraction for KNX 2 Byte DPT_Length_mm (mm)."""

    dpt_main_number = 7
    dpt_sub_number = 11
    value_type = "length_mm"
    unit = "mm"


class DPTUElCurrentmA(DPT2ByteUnsigned):
    """DPT 7.012 Abstraction for KNX 2 Byte DPTUElCurrentmA."""

    dpt_main_number = 7
    dpt_sub_number = 12
    value_type = "current"
    unit = "mA"


class DPTBrightness(DPT2ByteUnsigned):
    """DPT 7.013 DPT_Brightness (lux)."""

    dpt_main_number = 7
    dpt_sub_number = 13
    value_type = "brightness"
    unit = "lx"


class DPTColorTemperature(DPT2ByteUnsigned):
    """DPT 7.600 DPT_Color_Temperature (K)."""

    dpt_main_number = 7
    dpt_sub_number = 600
    value_type = "color_temperature"
    unit = "K"
