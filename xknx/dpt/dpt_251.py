"""Implementation of KNX RGBW color data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
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
