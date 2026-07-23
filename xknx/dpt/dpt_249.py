"""Implementation of KNX brightness / color temperature transition data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import RANGE_UINT8, DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary

RANGE_UINT16: dict[str, int] = {"value_min": 0, "value_max": 65_535}
RANGE_FADE_TIME_S: dict[str, float] = {
    "value_min": 0.0,
    "value_max": 6553.5,
    "resolution": 0.1,
}


@dataclass(slots=True)
class ColorTemperatureTransition(DPTComplexData):
    """
    Representation of an absolute color temperature and brightness transition.

    `fade_time`: transition time in seconds 0..6553.5 (resolution 0.1 s); None if invalid.
    `color_temperature`: int 0..65535 Kelvin; None if invalid.
    `brightness`: int 0..255; None if invalid.
    """

    fade_time: float | None = field(default=None, metadata=RANGE_FADE_TIME_S)
    color_temperature: int | None = field(default=None, metadata=RANGE_UINT16)
    brightness: int | None = field(default=None, metadata=RANGE_UINT8)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ColorTemperatureTransition:
        """Init from a dictionary."""
        result: dict[str, int | None] = {}
        for key in ("color_temperature", "brightness"):
            value = data.get(key)
            try:
                result[key] = int(value) if value is not None else None
            except (TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {key}: {err}") from err
        fade_time = data.get("fade_time")
        try:
            parsed_fade_time = float(fade_time) if fade_time is not None else None
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for fade_time: {err}") from err
        return cls(fade_time=parsed_fade_time, **result)

    def as_dict(self) -> dict[str, int | float | None]:
        """Create a JSON serializable dictionary."""
        return {
            "fade_time": self.fade_time,
            "color_temperature": self.color_temperature,
            "brightness": self.brightness,
        }


class DPTColorTemperatureTransition(DPTComplex[ColorTemperatureTransition]):
    """Abstraction for KNX 6 octet brightness/color temperature transition (DPT 249.600)."""

    data_type = ColorTemperatureTransition
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 249
    dpt_sub_number = 600
    value_type = "color_temperature_transition"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ColorTemperatureTransition:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)

        fade_time = round((raw[0] << 8 | raw[1]) * 0.1, 1)
        color_temperature = raw[2] << 8 | raw[3]
        brightness = raw[4]

        fade_time_valid = raw[5] >> 2 & 0b1
        color_temperature_valid = raw[5] >> 1 & 0b1
        brightness_valid = raw[5] & 0b1

        return ColorTemperatureTransition(
            color_temperature=color_temperature if color_temperature_valid else None,
            brightness=brightness if brightness_valid else None,
            fade_time=fade_time if fade_time_valid else None,
        )

    @classmethod
    def _to_knx(cls, value: ColorTemperatureTransition) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        fade_time_raw, color_temperature, brightness = 0, 0, 0
        fade_time_valid = False
        color_temperature_valid = False
        brightness_valid = False

        if value.fade_time is not None:
            if not 0 <= value.fade_time <= 6553.5:
                raise ValueError(
                    f"Fade time out of range 0..6553.5 s: {value.fade_time}"
                )
            fade_time_raw = round(value.fade_time * 10)
            fade_time_valid = True

        if value.color_temperature is not None:
            color_temperature = value.color_temperature
            if not 0 <= color_temperature <= 65_535:
                raise ValueError(
                    f"Color temperature out of range 0..65535 K: {color_temperature}"
                )
            color_temperature_valid = True

        if value.brightness is not None:
            brightness = value.brightness
            if not 0 <= brightness <= 255:
                raise ValueError(f"Brightness out of range 0..255: {brightness}")
            brightness_valid = True

        return DPTArray(
            (
                fade_time_raw >> 8,
                fade_time_raw & 0xFF,
                color_temperature >> 8,
                color_temperature & 0xFF,
                brightness,
                fade_time_valid << 2 | color_temperature_valid << 1 | brightness_valid,
            )
        )
