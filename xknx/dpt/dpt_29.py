"""Implementation of Basic KNX 8-Byte signed (2's complement) values."""

from __future__ import annotations

from .dpt import DPTNumeric, DPTStructIntMixin


class DPT8ByteSigned(DPTStructIntMixin, DPTNumeric):
    """
    Abstraction for KNX 8 Byte "64-bit signed".

    DPT 29.***
    """

    dpt_main_number = 29
    dpt_sub_number: int | None = None
    payload_length = 8
    value_type = "8byte_signed"

    value_min = -9_223_372_036_854_775_808
    value_max = 9_223_372_036_854_775_807
    resolution = 1

    _struct_format = ">q"


class DPTActiveEnergy8Byte(DPT8ByteSigned):
    """DPT 29.010 DPT_Active_Energy_V64."""

    dpt_main_number = 29
    dpt_sub_number = 10
    value_type = "active_energy_8byte"
    unit = "Wh"
    ha_device_class = "energy"


class DPTApparantEnergy8Byte(DPT8ByteSigned):
    """DPT 29.011 DPT_Apparant_Energy_V64 (VAh)."""

    dpt_main_number = 29
    dpt_sub_number = 11
    value_type = "apparant_energy_8byte"
    unit = "VAh"


class DPTReactiveEnergy8Byte(DPT8ByteSigned):
    """DPT 29.012 DPT_Reactive_Energy_V64 (VARh)."""

    dpt_main_number = 29
    dpt_sub_number = 12
    value_type = "reactive_energy_8byte"
    unit = "VARh"
