"""Implementation of the KNX date data point."""
from __future__ import annotations

from typing import NamedTuple

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class XYYColor(NamedTuple):
    """
    Representation of XY color with brightness.

    `color`: tuple(x-axis, y-axis) each 0..1; None if invalid.
    `brigtness`: int 0..255; None if invalid.
    tuple(tuple(float, float) | None, int | None)
    """

    color: tuple[float, float] | None = None
    brightness: int | None = None


class DPTColorXYY(DPTBase):
    """Abstraction for KNX 6 octet color xyY (DPT 242.600)."""

    payload_length = 6

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> XYYColor:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)

        x_axis = raw[0] << 8 | raw[1]
        y_axis = raw[2] << 8 | raw[3]
        brightness = raw[4]

        color_valid = raw[5] >> 1 & 0b1
        brightness_valid = raw[5] & 0b1

        return XYYColor(
            color=(x_axis / 0xFFFF, y_axis / 0xFFFF) if color_valid else None,
            brightness=brightness if brightness_valid else None,
        )

    @classmethod
    def to_knx(
        cls, value: XYYColor | tuple[tuple[float, float] | None, int | None]
    ) -> tuple[int, int, int, int, int, int]:
        """Serialize to KNX/IP raw data."""
        try:
            if not isinstance(value, XYYColor):
                value = XYYColor(*value)
            color_valid = False
            brightness_valid = False
            x_axis, y_axis, brightness = 0, 0, 0

            if value.color is not None:
                for _ in (axis for axis in value.color if not 0 <= axis <= 1):
                    raise ValueError
                color_valid = True
                x_axis, y_axis = (round(axis * 0xFFFF) for axis in value.color)

            if value.brightness is not None:
                if not 0 <= value.brightness <= 255:
                    raise ValueError
                brightness_valid = True
                brightness = int(value.brightness)

            return (
                x_axis >> 8,
                x_axis & 0xFF,
                y_axis >> 8,
                y_axis & 0xFF,
                brightness,
                color_valid << 1 | brightness_valid,
            )
        except (ValueError, TypeError):
            raise ConversionError("Could not serialize %s" % cls.__name__, value=value)
