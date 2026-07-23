"""Implementation of KNX RGBW relative control data point type."""

from __future__ import annotations

from dataclasses import dataclass, field

from .dpt import DPTComplex
from .dpt_1 import Step
from .dpt_3 import ControlDimming
from .helpers.metadata import RANGE_STEP_CODE
from .helpers.relative_control import (
    _RelativeControlDimming,
    pack_control_dimming,
    unpack_control_dimming,
)
from .payload import DPTArray, DPTBinary


@dataclass
class _RelativeControlRGBWDictSchemaFields:
    """Flat field definitions used for RelativeControlRGBW.get_dict_schema()."""

    red_control: Step | None = None
    red_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)
    green_control: Step | None = None
    green_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)
    blue_control: Step | None = None
    blue_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)
    white_control: Step | None = None
    white_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)


@dataclass(slots=True)
class RelativeControlRGBW(_RelativeControlDimming):
    """
    Representation of a relative RGBW color control.

    `red`, `green`, `blue`, `white`: ControlDimming; None if invalid.
    """

    red: ControlDimming | None = None
    green: ControlDimming | None = None
    blue: ControlDimming | None = None
    white: ControlDimming | None = None

    _dict_schema_fields_class = _RelativeControlRGBWDictSchemaFields


class DPTRelativeControlRGBW(DPTComplex[RelativeControlRGBW]):
    """Abstraction for KNX 5 octet relative RGBW control (DPT 252.600)."""

    data_type = RelativeControlRGBW
    payload_type = DPTArray
    payload_length = 5
    dpt_main_number = 252
    dpt_sub_number = 600
    value_type = "relative_control_rgbw"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RelativeControlRGBW:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        red_valid = raw[4] >> 3 & 0b1
        green_valid = raw[4] >> 2 & 0b1
        blue_valid = raw[4] >> 1 & 0b1
        white_valid = raw[4] & 0b1

        return RelativeControlRGBW(
            red=unpack_control_dimming(raw[0]) if red_valid else None,
            green=unpack_control_dimming(raw[1]) if green_valid else None,
            blue=unpack_control_dimming(raw[2]) if blue_valid else None,
            white=unpack_control_dimming(raw[3]) if white_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: RelativeControlRGBW) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                pack_control_dimming(value.red),
                pack_control_dimming(value.green),
                pack_control_dimming(value.blue),
                pack_control_dimming(value.white),
                (value.red is not None) << 3
                | (value.green is not None) << 2
                | (value.blue is not None) << 1
                | (value.white is not None),
            )
        )
