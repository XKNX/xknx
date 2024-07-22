"""Implementation of KNX 1-Bit KNX values."""

from __future__ import annotations

from .dpt import DPTEnum, DPTEnumData, EnumDataT
from .payload import DPTBinary


class DPT1BitEnum(DPTEnum[EnumDataT]):
    """Base class for KNX 1-Bit values encoded as Enums."""

    payload_type = DPTBinary
    payload_length = 1
    dpt_main_number = 1


class Step(DPTEnumData):
    """Enum for dimming control."""

    DECREASE = False
    INCREASE = True


class DPTStep(DPT1BitEnum[Step]):
    """
    Abstraction for KNX 1-Bit step value.

    DPT 1.007
    """

    dpt_main_number = 1
    dpt_sub_number = 7
    value_type = "step"
    data_type = Step

    @classmethod
    def _to_knx(cls, value: Step) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class UpDown(DPTEnumData):
    """Enum for up/down."""

    UP = False
    DOWN = True


class DPTUpDown(DPT1BitEnum[UpDown]):
    """
    Abstraction for KNX 1-Bit up/down value.

    DPT 1.008
    """

    dpt_main_number = 1
    dpt_sub_number = 8
    value_type = "up_down"
    data_type = UpDown

    @classmethod
    def _to_knx(cls, value: UpDown) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class HeatCool(DPTEnumData):
    """Enum for heat/cool."""

    COOL = False
    HEAT = True


class DPTHeatCool(DPT1BitEnum[HeatCool]):
    """
    Abstraction for KNX 1-Bit heat/cool value.

    DPT 1.100
    """

    dpt_main_number = 1
    dpt_sub_number = 100
    value_type = "heat_cool"
    data_type = HeatCool

    @classmethod
    def _to_knx(cls, value: HeatCool) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)
