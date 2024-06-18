"""Implementation of Basic KNX 4-Byte unsigned integer values."""

from __future__ import annotations

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric
from .payload import DPTArray, DPTBinary


class DPT4ByteUnsigned(DPTNumeric):
    """
    Abstraction for KNX 4 Byte "32-bit unsigned".

    DPT 12.***
    """

    dpt_main_number = 12
    dpt_sub_number: int | None = None
    value_type = "4byte_unsigned"
    payload_length = 4

    value_min = 0
    value_max = 4294967295
    resolution = 1

    _struct_format = ">I"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        try:
            return struct.unpack(cls._struct_format, bytes(raw))[0]  # type: ignore[no-any-return]
        except struct.error as err:
            raise ConversionError(f"Could not parse {cls.__name__}", raw=raw) from err

    @classmethod
    def to_knx(cls, value: int | float) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return DPTArray(struct.pack(cls._struct_format, knx_value))
        except (ValueError, struct.error) as err:
            raise ConversionError(
                f"Could not serialize {cls.__name__}", value=value
            ) from err

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPTValue4Ucount(DPT4ByteUnsigned):
    """DPT 12.001 DPT_Value_4_Ucount."""

    dpt_main_number = 12
    dpt_sub_number = 1
    value_type = "pulse_4_ucount"
    unit = "counter pulses"


class DPTLongTimePeriodSec(DPT4ByteUnsigned):
    """DPT 12.100 DPT_LongTimePeriod_Sec (seconds)."""

    dpt_main_number = 12
    dpt_sub_number = 100
    value_type = "long_time_period_sec"
    unit = "s"


class DPTLongTimePeriodMin(DPT4ByteUnsigned):
    """DPT 12.101 DPT_LongTimePeriod_Min (minutes)."""

    dpt_main_number = 12
    dpt_sub_number = 101
    value_type = "long_time_period_min"
    unit = "min"


class DPTLongTimePeriodHrs(DPT4ByteUnsigned):
    """DPT 12.102 DPT_LongTimePeriod_Hrs (hours)."""

    dpt_main_number = 12
    dpt_sub_number = 102
    value_type = "long_time_period_hrs"
    unit = "h"


class DPTVolumeLiquidLitre(DPT4ByteUnsigned):
    """DPT 12.1200 DPT_VolumeLiquid_Litre (water/gas total consumption)."""

    dpt_main_number = 12
    dpt_sub_number = 1200
    value_type = "volume_liquid_litre"
    unit = "L"


class DPTVolumeM3(DPT4ByteUnsigned):
    """DPT 12.1201 DPT_Volume_m3 (water/gas total consumption volume)."""

    dpt_main_number = 12
    dpt_sub_number = 1201
    value_type = "volume_m3"
    unit = "m³"
