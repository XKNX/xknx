"""Unit test for KNX light transition and relative color control DPTs."""

from typing import Any

import pytest

from xknx.dpt import (
    ColorTemperatureControl,
    ColorTemperatureTransition,
    DPTArray,
    DPTColorTemperatureControl,
    DPTColorTemperatureTransition,
    DPTColorXYYTransition,
    DPTRelativeControlRGB,
    DPTRelativeControlRGBW,
    DPTRelativeControlXYY,
    RelativeControlRGB,
    RelativeControlRGBW,
    RelativeControlXYY,
    XYYColorTransition,
)
from xknx.dpt.dpt_1 import Step
from xknx.dpt.dpt_3 import ControlDimming
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestXYYColorTransition:
    """Test XYYColorTransition class and DPTColorXYYTransition (243.600)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                XYYColorTransition(color=(0, 0), brightness=0, fade_time=0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03),
            ),
            (
                XYYColorTransition(color=(1, 1), brightness=255, fade_time=6553.5),
                (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03),
            ),
            (
                XYYColorTransition(color=None, brightness=0, fade_time=1.0),
                (0x00, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01),
            ),
            (
                XYYColorTransition(color=(0, 0), brightness=None, fade_time=0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02),
            ),
            (
                XYYColorTransition(color=None, brightness=None, fade_time=0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
        ],
    )
    def test_value(self, value: XYYColorTransition, raw: tuple[int]) -> None:
        """Test DPTColorXYYTransition parsing and streaming."""
        knx_value = DPTColorXYYTransition.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorXYYTransition.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTColorXYYTransition parsing from a dict."""
        knx_value = DPTColorXYYTransition.to_knx(
            {"x_axis": 0.2, "y_axis": 0.2, "brightness": 128, "fade_time": 1.0}
        )
        assert knx_value == DPTArray((0x00, 0x0A, 0x33, 0x33, 0x33, 0x33, 0x80, 0x03))

    @pytest.mark.parametrize(
        ("color", "brightness", "fade_time"),
        [
            ((-0.1, 0), 0, 0),
            ((0, 0), -1, 0),
            ((0, 0), 0, -0.1),
            ((0, 0), 0, 6553.6),
        ],
    )
    def test_to_knx_limits(
        self,
        color: tuple[float, float],
        brightness: int | None,
        fade_time: float,
    ) -> None:
        """Test initialization of DPTColorXYYTransition with wrong value."""
        value = XYYColorTransition(
            color=color, brightness=brightness, fade_time=fade_time
        )
        with pytest.raises(ConversionError):
            DPTColorXYYTransition.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTColorXYYTransition parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorXYYTransition.from_knx(DPTArray((0x00,) * 7))

    def test_from_dict_requires_fade_time(self) -> None:
        """Test that fade_time is required when parsing from a dict."""
        with pytest.raises(ConversionError):
            DPTColorXYYTransition.to_knx({"x_axis": 0.2, "y_axis": 0.2})

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema - fade_time is required and carries a resolution."""
        assert DPTColorXYYTransition.get_dict_schema() == [
            {
                "name": "fade_time",
                "type": "float",
                "required": True,
                "value_min": 0.0,
                "value_max": 6553.5,
                "resolution": 0.1,
            },
            {
                "name": "x_axis",
                "type": "float",
                "required": False,
                "value_min": 0.0,
                "value_max": 1.0,
            },
            {
                "name": "y_axis",
                "type": "float",
                "required": False,
                "value_min": 0.0,
                "value_max": 1.0,
            },
            {
                "name": "brightness",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 255,
            },
        ]


class TestColorTemperatureTransition:
    """Test ColorTemperatureTransition class and DPTColorTemperatureTransition (249.600)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                ColorTemperatureTransition(
                    color_temperature=3000, brightness=128, fade_time=0.5
                ),
                (0x00, 0x05, 0x0B, 0xB8, 0x80, 0x07),
            ),
            (
                ColorTemperatureTransition(
                    color_temperature=0, brightness=0, fade_time=0.0
                ),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x07),
            ),
            (
                ColorTemperatureTransition(
                    color_temperature=65_535, brightness=255, fade_time=6553.5
                ),
                (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x07),
            ),
            (
                ColorTemperatureTransition(
                    color_temperature=None, brightness=None, fade_time=None
                ),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                ColorTemperatureTransition(
                    color_temperature=3000, brightness=None, fade_time=None
                ),
                (0x00, 0x00, 0x0B, 0xB8, 0x00, 0x02),
            ),
        ],
    )
    def test_value(self, value: ColorTemperatureTransition, raw: tuple[int]) -> None:
        """Test DPTColorTemperatureTransition parsing and streaming."""
        knx_value = DPTColorTemperatureTransition.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorTemperatureTransition.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTColorTemperatureTransition parsing from a dict."""
        knx_value = DPTColorTemperatureTransition.to_knx(
            {"color_temperature": 3000, "brightness": 128, "fade_time": 0.5}
        )
        assert knx_value == DPTArray((0x00, 0x05, 0x0B, 0xB8, 0x80, 0x07))

    @pytest.mark.parametrize(
        ("color_temperature", "brightness", "fade_time"),
        [
            (-1, 0, 0),
            (65_536, 0, 0),
            (0, -1, 0),
            (0, 256, 0),
            (0, 0, -0.1),
            (0, 0, 6553.6),
        ],
    )
    def test_to_knx_limits(
        self,
        color_temperature: int | None,
        brightness: int | None,
        fade_time: float | None,
    ) -> None:
        """Test initialization of DPTColorTemperatureTransition with wrong value."""
        value = ColorTemperatureTransition(
            color_temperature=color_temperature,
            brightness=brightness,
            fade_time=fade_time,
        )
        with pytest.raises(ConversionError):
            DPTColorTemperatureTransition.to_knx(value)

    def test_fade_time_optional(self) -> None:
        """Test that fade_time may be omitted / None - Time Period marked invalid."""
        knx_value = DPTColorTemperatureTransition.to_knx(
            {"color_temperature": 3000, "brightness": 128}
        )
        assert knx_value == DPTArray((0x00, 0x00, 0x0B, 0xB8, 0x80, 0x03))
        assert DPTColorTemperatureTransition.from_knx(knx_value) == (
            ColorTemperatureTransition(
                color_temperature=3000, brightness=128, fade_time=None
            )
        )

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTColorTemperatureTransition parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorTemperatureTransition.from_knx(DPTArray((0x00,) * 5))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema - fade_time is optional and carries a resolution."""
        assert DPTColorTemperatureTransition.get_dict_schema() == [
            {
                "name": "fade_time",
                "type": "float",
                "required": False,
                "value_min": 0.0,
                "value_max": 6553.5,
                "resolution": 0.1,
            },
            {
                "name": "color_temperature",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 65_535,
            },
            {
                "name": "brightness",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 255,
            },
        ]


class TestColorTemperatureControl:
    """Test ColorTemperatureControl class and DPTColorTemperatureControl (250.600)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                ColorTemperatureControl(
                    ControlDimming(Step.INCREASE, 5), ControlDimming(Step.DECREASE, 3)
                ),
                (0x0D, 0x03, 0x03),
            ),
            (
                ColorTemperatureControl(ControlDimming(Step.INCREASE, 5), None),
                (0x0D, 0x00, 0x02),
            ),
            (
                ColorTemperatureControl(None, ControlDimming(Step.DECREASE, 3)),
                (0x00, 0x03, 0x01),
            ),
            (
                ColorTemperatureControl(None, None),
                (0x00, 0x00, 0x00),
            ),
        ],
    )
    def test_value(self, value: ColorTemperatureControl, raw: tuple[int]) -> None:
        """Test DPTColorTemperatureControl parsing and streaming."""
        knx_value = DPTColorTemperatureControl.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorTemperatureControl.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTColorTemperatureControl parsing from a dict."""
        knx_value = DPTColorTemperatureControl.to_knx(
            {
                "color_temperature_control": "increase",
                "color_temperature_step_code": 5,
            }
        )
        assert knx_value == DPTArray((0x0D, 0x00, 0x02))

    def test_from_dict_incomplete(self) -> None:
        """Test from_dict requires both control and step_code together."""
        with pytest.raises(ConversionError):
            DPTColorTemperatureControl.to_knx({"color_temperature_control": "increase"})

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTColorTemperatureControl parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorTemperatureControl.from_knx(DPTArray((0x00, 0x00)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTColorTemperatureControl."""
        assert DPTColorTemperatureControl.get_dict_schema() == [
            {
                "name": "color_temperature_control",
                "type": "enum",
                "required": False,
                "options": ["decrease", "increase"],
            },
            {
                "name": "color_temperature_step_code",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 7,
            },
            {
                "name": "brightness_control",
                "type": "enum",
                "required": False,
                "options": ["decrease", "increase"],
            },
            {
                "name": "brightness_step_code",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 7,
            },
        ]


class TestRelativeControlRGBW:
    """Test RelativeControlRGBW class and DPTRelativeControlRGBW (252.600)."""

    def test_value(self) -> None:
        """Test DPTRelativeControlRGBW parsing and streaming."""
        value = RelativeControlRGBW(
            red=ControlDimming(Step.INCREASE, 3),
            green=None,
            blue=ControlDimming(Step.DECREASE, 7),
            white=None,
        )
        raw = (0x0B, 0x00, 0x07, 0x00, 0x0A)
        knx_value = DPTRelativeControlRGBW.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRelativeControlRGBW.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTRelativeControlRGBW parsing from a dict."""
        knx_value = DPTRelativeControlRGBW.to_knx(
            {"red_control": "increase", "red_step_code": 3}
        )
        assert knx_value == DPTArray((0x0B, 0x00, 0x00, 0x00, 0x08))

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRelativeControlRGBW parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRelativeControlRGBW.from_knx(DPTArray((0x00,) * 4))


class TestRelativeControlXYY:
    """Test RelativeControlXYY class and DPTRelativeControlXYY (253.600)."""

    def test_value(self) -> None:
        """Test DPTRelativeControlXYY parsing and streaming."""
        value = RelativeControlXYY(
            saturation=ControlDimming(Step.INCREASE, 1),
            colour=None,
            brightness=ControlDimming(Step.DECREASE, 4),
        )
        raw = (0x09, 0x00, 0x04, 0x05)
        knx_value = DPTRelativeControlXYY.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRelativeControlXYY.from_knx(knx_value) == value

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRelativeControlXYY parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRelativeControlXYY.from_knx(DPTArray((0x00, 0x00, 0x00)))


class TestRelativeControlRGB:
    """Test RelativeControlRGB class and DPTRelativeControlRGB (254.600)."""

    def test_value(self) -> None:
        """Test DPTRelativeControlRGB parsing and streaming - no mask byte."""
        value = RelativeControlRGB(
            red=ControlDimming(Step.INCREASE, 1),
            green=ControlDimming(Step.DECREASE, 2),
            blue=ControlDimming(Step.INCREASE, 7),
        )
        raw = (0x09, 0x02, 0x0F)
        knx_value = DPTRelativeControlRGB.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRelativeControlRGB.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTRelativeControlRGB parsing from a dict, all fields required."""
        knx_value = DPTRelativeControlRGB.to_knx(
            {
                "red_control": "increase",
                "red_step_code": 1,
                "green_control": "decrease",
                "green_step_code": 2,
                "blue_control": "increase",
                "blue_step_code": 7,
            }
        )
        assert knx_value == DPTArray((0x09, 0x02, 0x0F))

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"red_control": "increase", "red_step_code": 1},
        ],
    )
    def test_to_knx_from_dict_incomplete(self, data: dict[str, Any]) -> None:
        """Test DPTRelativeControlRGB requires all three fields."""
        with pytest.raises(ConversionError):
            DPTRelativeControlRGB.to_knx(data)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRelativeControlRGB parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRelativeControlRGB.from_knx(DPTArray((0x00, 0x00)))
