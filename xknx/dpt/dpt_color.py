"""Implementation of the KNX date data point."""

from __future__ import annotations

from typing import TypedDict

from xknx.exceptions import ConversionError

from .dpt import DPTDict
from .payload import DPTArray, DPTBinary


class XYYColor(TypedDict, total=False):
    """
    Representation of XY color with brightness.

    `x_axis`, `y-axis`: each float 0..1; None if invalid.
    `brightness`: int 0..255; None if invalid.
    """

    x_axis: float | None
    y_axis: float | None
    brightness: int | None


class DPTColorXYY(DPTDict[XYYColor]):
    """Abstraction for KNX 6 octet color xyY (DPT 242.600)."""

    payload_type = DPTArray
    payload_length = 6

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
            # round to 5 digits for better readability but still preserving precision
            x_axis=round(x_axis_int / 0xFFFF, 5) if color_valid else None,
            y_axis=round(y_axis_int / 0xFFFF, 5) if color_valid else None,
            brightness=brightness if brightness_valid else None,
        )

    @classmethod
    # def to_knx(
    #     cls, value: XYYColor | tuple[tuple[float, float] | None, int | None]
    # ) -> DPTArray:
    def to_knx(cls, value: XYYColor) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            color_valid = False
            brightness_valid = False
            x_axis, y_axis, brightness = 0, 0, 0

            _x = value.get("x_axis")
            _y = value.get("y_axis")
            _brightness = value.get("brightness")

            if _x is not None and _y is not None:
                if (not 0 <= _x <= 1) or (not 0 <= _y <= 1):
                    raise ValueError("Color out of range")
                color_valid = True
                x_axis = round(_x * 0xFFFF)
                y_axis = round(_y * 0xFFFF)

            if _brightness is not None:
                if not 0 <= _brightness <= 255:
                    raise ValueError("Brightness out of range")
                brightness_valid = True
                brightness = int(_brightness)

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
        except (KeyError, ValueError, TypeError) as err:
            raise ConversionError(
                f"Could not serialize {cls.__name__}", value=value, error=err
            ) from err
