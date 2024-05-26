"""Implementation of the KNX date data point."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass
class RGBColor(DPTComplexData):
    """
    Representation of RGB color.

    `red`: int 0..255
    `green`: int 0..255
    `blue`: int 0..255
    """

    red: int
    green: int
    blue: int

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RGBColor:
        """Init from a dictionary."""
        try:
            red = int(data["red"])
            green = int(data["green"])
            blue = int(data["blue"])
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err
        except (ValueError, TypeError) as err:
            raise ValueError(f"Invalid value for RGB color: {err}") from err

        return cls(red=red, green=green, blue=blue)

    def as_dict(self) -> dict[str, int]:
        """Create a JSON serializable dictionary."""
        return {
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
        }


class DPTColorRGB(DPTComplex[RGBColor]):
    """Abstraction for KNX 3 octet color RGB (DPT 232.600)."""

    data_type = RGBColor
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 232
    dpt_sub_number = 600
    value_type = "color_rgb"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RGBColor:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return RGBColor(
            red=raw[0],
            green=raw[1],
            blue=raw[2],
        )

    @classmethod
    def _to_knx(cls, value: RGBColor) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        colors: tuple[int, int, int] = (value.red, value.green, value.blue)
        for color in colors:
            if not 0 <= color <= 255:
                raise ValueError(f"Color value out of range 0..255: {value}")
        return DPTArray(colors)


@dataclass
class RGBWColor(DPTComplexData):
    """
    Representation of RGBW color.

    `red`: int 0..255; None if invalid
    `green`: int 0..255; None if invalid
    `blue`: int 0..255; None if invalid
    `white`: int 0..255; None if invalid
    """

    red: int | None = None
    green: int | None = None
    blue: int | None = None
    white: int | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, int]) -> RGBWColor:
        """Init from a dictionary."""
        result = {}
        for color in ("red", "green", "blue", "white"):
            try:
                value = data.get(color)
                result[color] = int(value) if value is not None else None
            except AttributeError as err:
                raise ValueError(f"Invalid value for color {color}: {err}") from err
            except ValueError as err:
                raise ValueError(f"Invalid value for color {color}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "red": self.red,
            "green": self.green,
            "blue": self.blue,
            "white": self.white,
        }

    def __or__(self, other: RGBWColor) -> RGBWColor:
        """Merge two RGBWColor objects using only valid values."""
        return RGBWColor(
            red=other.red if other.red is not None else self.red,
            green=other.green if other.green is not None else self.green,
            blue=other.blue if other.blue is not None else self.blue,
            white=other.white if other.white is not None else self.white,
        )


class DPTColorRGBW(DPTComplex[RGBWColor]):
    """Abstraction for KNX 6 octet color RGBW (DPT 251.600)."""

    data_type = RGBWColor
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 251
    dpt_sub_number = 600
    value_type = "color_rgbw"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> RGBWColor:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        red_valid = raw[5] >> 3 & 0b1
        green_valid = raw[5] >> 2 & 0b1
        blue_valid = raw[5] >> 1 & 0b1
        white_valid = raw[5] & 0b1
        return RGBWColor(
            red=raw[0] if red_valid else None,
            green=raw[1] if green_valid else None,
            blue=raw[2] if blue_valid else None,
            white=raw[3] if white_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: RGBWColor) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        for color in (value.red, value.green, value.blue, value.white):
            if color is None:
                continue
            if not 0 <= color <= 255:
                raise ValueError(f"Color value out of range 0..255: {value}")
        return DPTArray(
            (
                value.red if value.red is not None else 0x00,
                value.green if value.green is not None else 0x00,
                value.blue if value.blue is not None else 0x00,
                value.white if value.white is not None else 0x00,
                0x00,  # reserved
                (
                    (value.red is not None) << 3
                    | (value.green is not None) << 2
                    | (value.blue is not None) << 1
                    | (value.white is not None)
                ),
            )
        )


@dataclass
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
