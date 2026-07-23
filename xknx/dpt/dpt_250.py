"""Implementation of KNX brightness / color temperature relative control data point type."""

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


@dataclass
class _ColorTemperatureControlDictSchemaFields:
    """Flat field definitions used for ColorTemperatureControl.get_dict_schema()."""

    color_temperature_control: Step | None = None
    color_temperature_step_code: int | None = field(
        default=None, metadata=RANGE_STEP_CODE
    )
    brightness_control: Step | None = None
    brightness_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)


@dataclass(slots=True)
class ColorTemperatureControl(DPTComplexData):
    """
    Representation of a relative color temperature and brightness control.

    `color_temperature`: ControlDimming; None if invalid.
    `brightness`: ControlDimming; None if invalid.
    """

    color_temperature: ControlDimming | None = None
    brightness: ControlDimming | None = None

    _dict_schema_fields_class = _ColorTemperatureControlDictSchemaFields

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ColorTemperatureControl:
        """Init from a dictionary."""
        result: dict[str, ControlDimming | None] = {}
        for key in ("color_temperature", "brightness"):
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
            ("color_temperature", self.color_temperature),
            ("brightness", self.brightness),
        ):
            result[f"{key}_control"] = (
                value.control.name.lower() if value is not None else None
            )
            result[f"{key}_step_code"] = value.step_code if value is not None else None
        return result


class DPTColorTemperatureControl(DPTComplex[ColorTemperatureControl]):
    """Abstraction for KNX 3 octet brightness/color temperature control (DPT 250.600)."""

    data_type = ColorTemperatureControl
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 250
    dpt_sub_number = 600
    value_type = "color_temperature_control"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ColorTemperatureControl:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        color_temperature_valid = raw[2] >> 1 & 0b1
        brightness_valid = raw[2] & 0b1

        return ColorTemperatureControl(
            color_temperature=unpack_control_dimming(raw[0])
            if color_temperature_valid
            else None,
            brightness=unpack_control_dimming(raw[1]) if brightness_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: ColorTemperatureControl) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return DPTArray(
            (
                pack_control_dimming(value.color_temperature),
                pack_control_dimming(value.brightness),
                (value.color_temperature is not None) << 1
                | (value.brightness is not None),
            )
        )
