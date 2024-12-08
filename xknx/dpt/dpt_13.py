"""Implementation of Basic KNX 4-Byte signed (2's complement) values."""

from __future__ import annotations

from .dpt import DPTNumeric, DPTStructIntMixin


class DPT4ByteSigned(DPTStructIntMixin, DPTNumeric):
    """
    Abstraction for KNX 4 Byte "32-bit signed".

    DPT 13.***
    """

    dpt_main_number = 13
    dpt_sub_number: int | None = None
    value_type = "4byte_signed"
    payload_length = 4

    value_min = -2147483648
    value_max = 2147483647
    resolution = 1

    _struct_format = ">i"


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
