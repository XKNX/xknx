"""Implementation of KNX RGB relative control data point type."""

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
class _RelativeControlRGBDictSchemaFields:
    """Flat field definitions used for RelativeControlRGB.get_dict_schema()."""

    red_control: Step
    red_step_code: int = field(metadata=RANGE_STEP_CODE)
    green_control: Step
    green_step_code: int = field(metadata=RANGE_STEP_CODE)
    blue_control: Step
    blue_step_code: int = field(metadata=RANGE_STEP_CODE)


@dataclass(slots=True)
class RelativeControlRGB(_RelativeControlDimming):
    """
    Representation of a relative RGB color control.

    `red`, `green`, `blue`: ControlDimming.

    This DPT does not support marking single fields as invalid - all fields
    are always transmitted (required). Use `RelativeControlRGBW`
    (DPT 252.600) if per-field validity is needed.
    """

    red: ControlDimming
    green: ControlDimming
    blue: ControlDimming

    _dict_schema_fields_class = _RelativeControlRGBDictSchemaFields


class DPTRelativeControlRGB(DPTComplex[RelativeControlRGB]):
    """Abstraction for KNX 3 octet relative RGB control (DPT 254.600)."""

    data_type = RelativeControlRGB
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 254
    dpt_sub_number = 600
    value_type = "relative_control_rgb"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RelativeControlRGB:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return RelativeControlRGB(
            red=unpack_control_dimming(raw[0]),
            green=unpack_control_dimming(raw[1]),
            blue=unpack_control_dimming(raw[2]),
        )

    @classmethod
    def _to_knx(cls, value: RelativeControlRGB) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                pack_control_dimming(value.red),
                pack_control_dimming(value.green),
                pack_control_dimming(value.blue),
            )
        )
