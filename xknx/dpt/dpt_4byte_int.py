"""
Implementation of Basic KNX 4-Byte Signed and Unsigned Values.

They correspond the following KNX DPTs:
    12.yyy 4-byte/octet unsigned value, i.e. pulse counter
    13.yyy 4-byte/octet signed (2's complement), i.e. flow, energy
"""
from __future__ import annotations

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric


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
    def from_knx(cls, raw: tuple[int, ...]) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        try:
            return struct.unpack(cls._struct_format, bytes(raw))[0]  # type: ignore
        except struct.error:
            raise ConversionError(f"Could not parse {cls.__name__}", raw=raw)

    @classmethod
    def to_knx(cls, value: int | float) -> tuple[int, ...]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = int(value)
            if not cls._test_boundaries(knx_value):
                raise ValueError
            return tuple(struct.pack(cls._struct_format, knx_value))
        except (ValueError, struct.error):
            raise ConversionError(f"Could not serialize {cls.__name__}", value=value)

    @classmethod
    def _test_boundaries(cls, value: int) -> bool:
        """Test if value is within defined range for this object."""
        return cls.value_min <= value <= cls.value_max


class DPT4ByteSigned(DPT4ByteUnsigned):
    """
    Abstraction for KNX 4 Byte "32-bit signed".

    DPT 13.***
    """

    dpt_main_number = 13
    dpt_sub_number: int | None = None
    value_type = "4byte_signed"

    value_min = -2147483648
    value_max = 2147483647
    resolution = 1

    _struct_format = ">i"


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


class DPTValue4Count(DPT4ByteSigned):
    """DPT 13.001 DPT_Value_4_Count (pulse)."""

    dpt_main_number = 13
    dpt_sub_number = 1
    value_type = "pulse_4byte"
    unit = "counter pulses"


class DPTFlowRateM3H(DPT4ByteSigned):
    """DPT 13.002 DPT_FlowRate_m3/h (m³/h)."""

    dpt_main_number = 13
    dpt_sub_number = 2
    value_type = "flow_rate_m3h"
    unit = "m³/h"


class DPTActiveEnergy(DPT4ByteSigned):
    """DPT 13.010 DPT_ActiveEnergy (Wh)."""

    dpt_main_number = 13
    dpt_sub_number = 10
    value_type = "active_energy"
    unit = "Wh"
    ha_device_class = "energy"


class DPTApparantEnergy(DPT4ByteSigned):
    """DPT 13.011 DPT_ActiveEnergy (VAh)."""

    dpt_main_number = 13
    dpt_sub_number = 11
    value_type = "apparant_energy"
    unit = "VAh"


class DPTReactiveEnergy(DPT4ByteSigned):
    """DPT 13.012 DPT_ActiveEnergy (VARh)."""

    dpt_main_number = 13
    dpt_sub_number = 12
    value_type = "reactive_energy"
    unit = "VARh"


class DPTActiveEnergykWh(DPT4ByteSigned):
    """DPT 13.013 DPT_ActiveEnergy_kWh (kWh)."""

    dpt_main_number = 13
    dpt_sub_number = 13
    value_type = "active_energy_kwh"
    unit = "kWh"
    ha_device_class = "energy"


class DPTApparantEnergykVAh(DPT4ByteSigned):
    """DPT 13.014 DPT_ActiveEnergy_kVAh (kVAh)."""

    dpt_main_number = 13
    dpt_sub_number = 14
    value_type = "apparant_energy_kvah"
    unit = "kVAh"


class DPTReactiveEnergykVARh(DPT4ByteSigned):
    """DPT 13.015 DPT_ActiveEnergy (kVARh)."""

    dpt_main_number = 13
    dpt_sub_number = 15
    value_type = "reactive_energy_kvarh"
    unit = "kVARh"


class DPTActiveEnergyMWh(DPT4ByteSigned):
    """DPT 13.016 DPT_ActiveEnergy_MWh (MWh)."""

    dpt_main_number = 13
    dpt_sub_number = 16
    value_type = "active_energy_mwh"
    unit = "MWh"


class DPTLongDeltaTimeSec(DPT4ByteSigned):
    """DPT 13.100 DPT_LongDeltaTimeSec (s)."""

    dpt_main_number = 13
    dpt_sub_number = 100
    value_type = "long_delta_timesec"
    unit = "s"
