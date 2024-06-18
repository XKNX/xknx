"""Implementation of KNX XYY color data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class XYYColor(DPTComplexData):
    """
    Representation of XY color with brightness.

    `color`: tuple(x-axis, y-axis) each 0..1; None if invalid.
    `brightness`: int 0..255; None if invalid.
    """

    color: tuple[float, float] | None = None
    brightness: int | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> XYYColor:
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
            raise ValueError("Both x_axis and y_axis must be provided")

        if brightness is not None:
            try:
                brightness = int(brightness)
            except ValueError as err:
                raise ValueError(f"Invalid value for brightness: {err}") from err

        return cls(color=color, brightness=brightness)

    def as_dict(self) -> dict[str, int | float | None]:
        """Create a JSON serializable dictionary."""
        return {
            "x_axis": self.color[0] if self.color is not None else None,
            "y_axis": self.color[1] if self.color is not None else None,
            "brightness": self.brightness,
        }

    def __or__(self, other: XYYColor) -> XYYColor:
        """Merge two XYYColor objects using only valid values."""
        return XYYColor(
            color=other.color if other.color is not None else self.color,
            brightness=other.brightness
            if other.brightness is not None
            else self.brightness,
        )


class DPTColorXYY(DPTComplex[XYYColor]):
    """Abstraction for KNX 6 octet color xyY (DPT 242.600)."""

    data_type = XYYColor
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 242
    dpt_sub_number = 600
    value_type = "color_xyy"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> XYYColor:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        x_axis_int = raw[0] << 8 | raw[1]
        y_axis_int = raw[2] << 8 | raw[3]
        brightness = raw[4]

        color_valid = raw[5] >> 1 & 0b1
        brightness_valid = raw[5] & 0b1

        return XYYColor(
            color=(
                # round to 5 digits for better readability but still preserving precision
                round(x_axis_int / 0xFFFF, 5),
                round(y_axis_int / 0xFFFF, 5),
            )
            if color_valid
            else None,
            brightness=brightness if brightness_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: XYYColor) -> DPTArray:
        """Serialize to KNX/IP raw data."""
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
                x_axis >> 8,
                x_axis & 0xFF,
                y_axis >> 8,
                y_axis & 0xFF,
                brightness,
                color_valid << 1 | brightness_valid,
            )
        )
