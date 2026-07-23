"""Implementation of KNX xyY relative control data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .dpt_1 import Step
from .dpt_3 import (
    RANGE_STEP_CODE,
    ControlDimming,
    pack_control_dimming,
    unpack_control_dimming,
)
from .payload import DPTArray, DPTBinary

_FIELDS = ("saturation", "colour", "brightness")


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
class RelativeControlXYY(DPTComplexData):
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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RelativeControlXYY:
        """Init from a dictionary."""
        result: dict[str, ControlDimming | None] = {}
        for key in _FIELDS:
            control = data.get(f"{key}_control")
            step_code = data.get(f"{key}_step_code")
            if control is not None and step_code is not None:
                try:
                    result[key] = ControlDimming(
                        control=Step.parse(control), step_code=int(step_code)
                    )
                except (TypeError, ValueError) as err:
                    raise ValueError(f"Invalid value for {key}: {err}") from err
            elif control is not None or step_code is not None:
                raise ValueError(
                    f"Provide both {key}_control and {key}_step_code, or neither"
                )
            else:
                result[key] = None
        return cls(**result)

    def as_dict(self) -> dict[str, int | str | None]:
        """Create a JSON serializable dictionary."""
        result: dict[str, int | str | None] = {}
        for key, value in (
            ("saturation", self.saturation),
            ("colour", self.colour),
            ("brightness", self.brightness),
        ):
            result[f"{key}_control"] = (
                value.control.name.lower() if value is not None else None
            )
            result[f"{key}_step_code"] = value.step_code if value is not None else None
        return result


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
