"""Implementation of KNX xyY color transition data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .helpers.metadata import RANGE_FADE_TIME_S, RANGE_UINT8
from .payload import DPTArray, DPTBinary


@dataclass
class _XYYColorTransitionDictSchemaFields:
    """Flat field definitions used for XYYColorTransition.get_dict_schema()."""

    fade_time: float = field(metadata=RANGE_FADE_TIME_S)
    x_axis: float | None = field(
        default=None, metadata={"value_min": 0.0, "value_max": 1.0}
    )
    y_axis: float | None = field(
        default=None, metadata={"value_min": 0.0, "value_max": 1.0}
    )
    brightness: int | None = field(default=None, metadata=RANGE_UINT8)


@dataclass(slots=True)
class XYYColorTransition(DPTComplexData):
    """
    Representation of a XY color transition with brightness.

    `fade_time`: transition time in seconds 0..6553.5 (resolution 0.1 s).
    `color`: tuple(x-axis, y-axis) each 0..1; None if invalid.
    `brightness`: int 0..255; None if invalid.
    """

    fade_time: float
    color: tuple[float, float] | None = None
    brightness: int | None = None

    _dict_schema_fields_class = _XYYColorTransitionDictSchemaFields

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> XYYColorTransition:
        """Init from a dictionary."""
        color = None
        brightness = data.get("brightness")
        x_axis = data.get("x_axis")
        y_axis = data.get("y_axis")

        if x_axis is not None and y_axis is not None:
            try:
                color = (float(x_axis), float(y_axis))
            except ValueError as err:
                raise ValueError(f"Invalid value for color axis: {err}") from err
        elif x_axis is not None or y_axis is not None:
            raise ValueError("Provide both x_axis and y_axis, or neither")

        if brightness is not None:
            try:
                brightness = int(brightness)
            except ValueError as err:
                raise ValueError(f"Invalid value for brightness: {err}") from err

        if "fade_time" not in data:
            raise ValueError("`fade_time` is required")
        try:
            fade_time = float(data["fade_time"])
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for fade_time: {err}") from err

        return cls(color=color, brightness=brightness, fade_time=fade_time)

    def as_dict(self) -> dict[str, int | float | None]:
        """Create a JSON serializable dictionary."""
        return {
            "fade_time": self.fade_time,
            "x_axis": self.color[0] if self.color is not None else None,
            "y_axis": self.color[1] if self.color is not None else None,
            "brightness": self.brightness,
        }


class DPTColorXYYTransition(DPTComplex[XYYColorTransition]):
    """Abstraction for KNX 8 octet xyY color transition (DPT 243.600)."""

    data_type = XYYColorTransition
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 243
    dpt_sub_number = 600
    value_type = "color_xyy_transition"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> XYYColorTransition:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        fade_time = round((raw[0] << 8 | raw[1]) * 0.1, 1)
        x_axis_int = raw[2] << 8 | raw[3]
        y_axis_int = raw[4] << 8 | raw[5]
        brightness = raw[6]

        color_valid = raw[7] >> 1 & 0b1
        brightness_valid = raw[7] & 0b1

        return XYYColorTransition(
            color=(
                round(x_axis_int / 0xFFFF, 5),
                round(y_axis_int / 0xFFFF, 5),
            )
            if color_valid
            else None,
            brightness=brightness if brightness_valid else None,
            fade_time=fade_time,
        )

    @classmethod
    def _to_knx(cls, value: XYYColorTransition) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.fade_time <= 6553.5:
            raise ValueError(f"Fade time out of range 0..6553.5 s: {value.fade_time}")
        fade_time_raw = round(value.fade_time * 10)

        x_axis, y_axis, brightness = 0, 0, 0
        color_valid = False
        brightness_valid = False

        if value.color is not None:
            for axis in value.color:
                if not 0 <= axis <= 1:
                    raise ValueError(
                        f"Color axis value out of range 0..1: {value.color}"
                    )
            x_axis, y_axis = (round(axis * 0xFFFF) for axis in value.color)
            color_valid = True

        if value.brightness is not None:
            brightness = value.brightness
            if not 0 <= brightness <= 255:
                raise ValueError(f"Brightness out of range 0..255: {brightness}")
            brightness_valid = True

        return DPTArray(
            (
                fade_time_raw >> 8,
                fade_time_raw & 0xFF,
                x_axis >> 8,
                x_axis & 0xFF,
                y_axis >> 8,
                y_axis & 0xFF,
                brightness,
                color_valid << 1 | brightness_valid,
            )
        )
