"""Implementation of KNX RGB relative control data point type."""

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

_FIELDS = ("red", "green", "blue")


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
class RelativeControlRGB(DPTComplexData):
    """
    Representation of a relative RGB color control.

    `red`, `green`, `blue`: ControlDimming.

    This DPT does not support marking single fields as invalid - all fields
    are always transmitted. Use `RelativeControlRGBW` (DPT 252.600) if
    per-field validity is needed.
    """

    red: ControlDimming
    green: ControlDimming
    blue: ControlDimming

    _dict_schema_fields_class = _RelativeControlRGBDictSchemaFields

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RelativeControlRGB:
        """Init from a dictionary."""
        result: dict[str, ControlDimming] = {}
        for key in _FIELDS:
            try:
                result[key] = ControlDimming(
                    control=Step.parse(data[f"{key}_control"]),
                    step_code=int(data[f"{key}_step_code"]),
                )
            except (KeyError, TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {key}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        result: dict[str, int | str] = {}
        for key, value in (
            ("red", self.red),
            ("green", self.green),
            ("blue", self.blue),
        ):
            result[f"{key}_control"] = value.control.name.lower()
            result[f"{key}_step_code"] = value.step_code
        return result


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
