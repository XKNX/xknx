"""Implementation of KNX 1-Bit KNX values."""

from __future__ import annotations

from enum import Enum

from .dpt import DPTEnum, EnumT
from .payload import DPTBinary


class DPT1BitEnum(DPTEnum[EnumT]):
    """Base class for KNX 1-Bit values encoded as Enums."""

    payload_type = DPTBinary
    payload_length = 1
    dpt_main_number = 1


class HeatCool(Enum):
    """Enum for heat/cool."""

    COOL = False
    HEAT = True


class DPTHeatCool(DPT1BitEnum[HeatCool]):
    """
    Abstraction for KNX 1-Bit heat/cool value.

    DPT 1.100
    """

    dpt_sub_number = 100
    value_type = "heat_cool"
    data_type = HeatCool

    @classmethod
    def _to_knx(cls, value: HeatCool) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)
