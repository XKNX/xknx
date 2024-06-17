"""Implementation of KNX RGB color data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
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
