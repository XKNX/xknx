"""Implementation of Basic KNX 2-Byte/octet values."""
from __future__ import annotations

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric


class DPT2ByteUnsigned(DPTNumeric):
    """
    Abstraction for KNX 2 Byte "2-octet unsigned value".

    Contains smaller counters, timers  etc.

    DPT 7.***
    """

    dpt_main_number = 7
    dpt_sub_number: int | None = None
    value_type = "2byte_unsigned"
    payload_length = 2

    value_min = 0
    value_max = 65535
    resolution = 1

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        return (raw[0] * 256) + raw[1]

    @classmethod
    def to_knx(cls, value: int | float) -> tuple[int, int]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return knx_value >> 8, knx_value & 0xFF
        except ValueError:
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

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


class DPTTimePeriod100Msec(DPT2ByteUnsigned):
    """DPT 7.004 DPT_TimePeriod100Msec (ms)."""

    dpt_main_number = 7
    dpt_sub_number = 4
    value_type = "time_period_100msec"
    unit = "ms"


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


class DPTPropDataType(DPT2ByteUnsigned):
    """DPT 7.010 DPT_PropDataType."""

    dpt_main_number = 7
    dpt_sub_number = 10
    value_type = "prop_data_type"


class DPTLengthMm(DPT2ByteUnsigned):
    """DPT 7.011 Abstraction for KNX 2 Byte DPT_Length_mm (mm)."""

    dpt_main_number = 7
    dpt_sub_number = 11
    value_type = "length_mm"
    unit = "mm"
    ha_device_class = "distance"


class DPTUElCurrentmA(DPT2ByteUnsigned):
    """DPT 7.012 Abstraction for KNX 2 Byte DPTUElCurrentmA."""

    dpt_main_number = 7
    dpt_sub_number = 12
    value_type = "current"
    unit = "mA"
    ha_device_class = "current"


class DPTBrightness(DPT2ByteUnsigned):
    """DPT 7.013 DPT_Brightness (lux)."""

    dpt_main_number = 7
    dpt_sub_number = 13
    value_type = "brightness"
    unit = "lx"
    ha_device_class = "illuminance"


class DPTColorTemperature(DPT2ByteUnsigned):
    """DPT 7.600 DPT_Color_Temperature (K)."""

    dpt_main_number = 7
    dpt_sub_number = 600
    value_type = "color_temperature"
    unit = "K"
