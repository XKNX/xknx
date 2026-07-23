"""Implementation of KNX xyY relative control data point type."""

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
class _RelativeControlXYYDictSchemaFields:
    """Flat field definitions used for RelativeControlXYY.get_dict_schema()."""

    saturation_control: Step | None = None
    saturation_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)
    colour_control: Step | None = None
    colour_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)
    brightness_control: Step | None = None
    brightness_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)


@dataclass(slots=True)
class RelativeControlXYY(_RelativeControlDimming):
    """
    Representation of a relative xyY color control.

    `saturation`: ControlDimming for the distance to the white point; None if invalid.
    `colour`: ControlDimming for the colour wavelength; None if invalid.
    `brightness`: ControlDimming; None if invalid.
    """

    saturation: ControlDimming | None = None
    colour: ControlDimming | None = None
    brightness: ControlDimming | None = None

    _dict_schema_fields_class = _RelativeControlXYYDictSchemaFields


class DPTRelativeControlXYY(DPTComplex[RelativeControlXYY]):
    """Abstraction for KNX 4 octet relative xyY control (DPT 253.600)."""

    data_type = RelativeControlXYY
    payload_type = DPTArray
    payload_length = 4
    dpt_main_number = 253
    dpt_sub_number = 600
    value_type = "relative_control_xyy"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RelativeControlXYY:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        saturation_valid = raw[3] >> 2 & 0b1
        colour_valid = raw[3] >> 1 & 0b1
        brightness_valid = raw[3] & 0b1

        return RelativeControlXYY(
            saturation=unpack_control_dimming(raw[0]) if saturation_valid else None,
            colour=unpack_control_dimming(raw[1]) if colour_valid else None,
            brightness=unpack_control_dimming(raw[2]) if brightness_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: RelativeControlXYY) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                pack_control_dimming(value.saturation),
                pack_control_dimming(value.colour),
                pack_control_dimming(value.brightness),
                (value.saturation is not None) << 2
                | (value.colour is not None) << 1
                | (value.brightness is not None),
            )
        )
