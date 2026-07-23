"""Implementation of KNX brightness / color temperature relative control data point type."""

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
class _ColorTemperatureControlDictSchemaFields:
    """Flat field definitions used for ColorTemperatureControl.get_dict_schema()."""

    color_temperature_control: Step | None = None
    color_temperature_step_code: int | None = field(
        default=None, metadata=RANGE_STEP_CODE
    )
    brightness_control: Step | None = None
    brightness_step_code: int | None = field(default=None, metadata=RANGE_STEP_CODE)


@dataclass(slots=True)
class ColorTemperatureControl(_RelativeControlDimming):
    """
    Representation of a relative color temperature and brightness control.

    `color_temperature`: ControlDimming; None if invalid.
    `brightness`: ControlDimming; None if invalid.
    """

    color_temperature: ControlDimming | None = None
    brightness: ControlDimming | None = None

    _dict_schema_fields_class = _ColorTemperatureControlDictSchemaFields


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
