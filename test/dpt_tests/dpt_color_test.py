"""Unit test for KNX color objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTColorRGB,
    DPTColorRGBW,
    DPTColorXYY,
    RGBColor,
    RGBWColor,
    XYYColor,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestRGBColor:
    """Test RGBColor class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"red": 0, "green": 128, "blue": 255}, RGBColor(0, 128, 255)),
            ({"red": 255, "green": 255, "blue": 255}, RGBColor(255, 255, 255)),
            ({"red": 0, "green": 0, "blue": 0}, RGBColor(0, 0, 0)),
        ],
    )
    def test_dict(self, data: dict[str, int], value: RGBColor) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RGBColor.from_dict(data)
        assert test_value == value
        assert value.as_dict() == data

    @pytest.mark.parametrize(
        "data",
        [
            # incomplete data
            {},
            {"red": 128},
            {"green": 128},
            {"blue": 128},
            {"red": 128, "green": 128},
            {"red": 128, "blue": 128},
            {"green": 128, "blue": 128},
            # invalid data
            {"red": "a", "green": 128, "blue": 128},
            {"red": 128, "green": "a", "blue": 128},
            {"red": 128, "green": 128, "blue": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            RGBColor.from_dict(data)


class TestDPTColorRGB:
    """Test class for KNX RGB-color objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (RGBColor(0, 0, 0), (0x00, 0x00, 0x00)),  # min values
            (RGBColor(255, 255, 255), (0xFF, 0xFF, 0xFF)),  # max values
            (RGBColor(128, 128, 128), (0x80, 0x80, 0x80)),  # mid values
        ],
    )
    def test_rgbcolor_value(self, value: RGBColor, raw: tuple[int]) -> None:
        """Test DPTColorRGB parsing and streaming."""
        knx_value = DPTColorRGB.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorRGB.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({"red": 128, "green": 128, "blue": 128}, (0x80, 0x80, 0x80)),
            ({"red": 255, "green": 255, "blue": 255}, (0xFF, 0xFF, 0xFF)),
        ],
    )
    def test_rgbcolor_to_knx_from_dict(
        self, value: dict[str, int], raw: tuple[int]
    ) -> None:
        """Test DPTColorRGB parsing from a dict."""
        knx_value = DPTColorRGB.to_knx(value)
        assert knx_value == DPTArray(raw)

    @pytest.mark.parametrize(
        ("red", "green", "blue"),
        [
            (-1, 0, 0),
            (0, -1, 0),
            (0, 0, -1),
            (256, 0, 0),
            (0, 256, 0),
            (0, 0, 256),
        ],
    )
    def test_rgbcolor_to_knx_limits(self, red: int, green: int, blue: int) -> None:
        """Test initialization of DPTColorRGB with wrong value."""
        value = RGBColor(red=red, green=green, blue=blue)
        with pytest.raises(ConversionError):
            DPTColorRGB.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            (0xFF, 0x4E, 0x12),
            1,
            ((0x00, 0xFF, 0x4E), 0x12),
            ((0xFF, 0x4E), (0x12, 0x00)),
            ((0, 0), "a"),
            ((0, 0), 0.4),
            RGBColor(red=0, green=0, blue="a"),
            RGBColor(red=4, green="a", blue=4),
            RGBColor(red="a", green=0, blue=1),
        ],
    )
    def test_rgbcolor_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTColorRGB parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTColorRGB.to_knx(value)

    def test_rgbcolor_wrong_value_from_knx(self) -> None:
        """Test DPTColorRGB parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorRGB.from_knx(DPTArray((0xFF, 0x4E, 0x12, 0x23)))
        with pytest.raises(CouldNotParseTelegram):
            DPTColorRGB.from_knx(DPTArray((0xFF, 0x4E)))


class TestRGBWColor:
    """Test RGBWColor class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"red": 128, "green": 128, "blue": 128, "white": 128},
                RGBWColor(128, 128, 128, 128),
            ),
            (
                {"red": 255, "green": 255, "blue": 255, "white": 255},
                RGBWColor(255, 255, 255, 255),
            ),
            ({"red": 128, "green": 128, "blue": 128}, RGBWColor(128, 128, 128)),
            ({"white": 50}, RGBWColor(None, None, None, 50)),
            ({}, RGBWColor()),
            (
                {"red": None, "green": None, "blue": None, "white": 255},
                RGBWColor(None, None, None, 255),
            ),
            (
                {"red": 128, "green": 128, "blue": 128, "white": None},
                RGBWColor(128, 128, 128, None),
            ),
            ({"red": None, "white": 255}, RGBWColor(None, None, None, 255)),
            ({"green": None, "white": 255}, RGBWColor(None, None, None, 255)),
            ({"red": 128}, RGBWColor(128, None, None, None)),
            ({"green": 128}, RGBWColor(None, 128, None, None)),
            ({"blue": 128}, RGBWColor(None, None, 128, None)),
            ({"red": 128, "white": 128}, RGBWColor(128, None, None, 128)),
            ({"green": 128, "white": 128}, RGBWColor(None, 128, None, 128)),
            ({"blue": 128, "white": 128}, RGBWColor(None, None, 128, 128)),
        ],
    )
    def test_dict(self, data: dict[str, int], value: RGBWColor) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RGBWColor.from_dict(data)
        assert test_value == value
        # fields default to `None`
        default_dict = {"red": None, "green": None, "blue": None, "white": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            # invalid data
            {"red": "a", "green": 128, "blue": 128, "white": 128},
            {"red": 128, "green": "a", "blue": 128, "white": 128},
            {"red": 128, "green": 128, "blue": "a", "white": 128},
            {"red": 128, "green": 128, "blue": 128, "white": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            RGBWColor.from_dict(data)

    def test_merge(self) -> None:
        """Test merging two RGBWColor objects."""
        color1 = RGBWColor(1, 1, 1, None)
        color2 = RGBWColor(None, None, None, 2)
        color3 = RGBWColor(3, None, None, 3)
        assert color1 | color2 == RGBWColor(1, 1, 1, 2)
        assert color2 | color1 == RGBWColor(1, 1, 1, 2)
        assert color1 | color3 == RGBWColor(3, 1, 1, 3)
        assert color3 | color1 == RGBWColor(1, 1, 1, 3)
        assert color2 | color3 == RGBWColor(3, None, None, 3)
        assert color3 | color2 == RGBWColor(3, None, None, 2)


class TestDPTColorRGBW:
    """Test class for KNX RGBW-color objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (RGBWColor(0, 0, 0, 0), (0x00, 0x00, 0x00, 0x00, 0, 0xF)),  # min values
            (RGBWColor(255, 255, 255, 255), (0xFF, 0xFF, 0xFF, 0xFF, 0, 0xF)),  # max
            (RGBWColor(None, 0, 0, 0), (0x00, 0x00, 0x00, 0x00, 0, 0x7)),  # red None
            (RGBWColor(0, 0, 0, None), (0x00, 0x00, 0x00, 0x00, 0, 0xE)),  # white None
            (RGBWColor(None, None, None, None), (0x00, 0x00, 0x00, 0x00, 0, 0)),
            (RGBWColor(128, 128, 128, 128), (0x80, 0x80, 0x80, 0x80, 0, 0b1111)),
            (RGBWColor(204, 204, 204, 204), (0xCC, 0xCC, 0xCC, 0xCC, 0, 0b1111)),
        ],
    )
    def test_rgbwcolor_value(self, value: RGBWColor, raw: tuple[int]) -> None:
        """Test DPTColorRGBW parsing and streaming."""
        knx_value = DPTColorRGBW.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorRGBW.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                {"red": 128, "green": 128, "blue": 128, "white": 128},
                (0x80, 0x80, 0x80, 0x80, 0, 0xF),
            ),
            (
                {"red": 204, "green": 204, "blue": 204, "white": 204},
                (0xCC, 0xCC, 0xCC, 0xCC, 0, 0xF),
            ),
            (
                {"red": 204, "green": 204, "blue": 204},
                (0xCC, 0xCC, 0xCC, 0x00, 0, 0xE),
            ),
        ],
    )
    def test_rgbwcolor_to_knx_from_dict(
        self, value: dict[str, int], raw: tuple[int]
    ) -> None:
        """Test DPTColorRGBW parsing from a dict."""
        knx_value = DPTColorRGBW.to_knx(value)
        assert knx_value == DPTArray(raw)

    @pytest.mark.parametrize(
        ("red", "green", "blue", "white"),
        [
            (-1, 0, 0, 0),
            (0, -1, 0, 0),
            (0, 0, -1, 0),
            (0, 0, 0, -1),
            (256, 0, 0, 0),
            (0, 256, 0, 0),
            (0, 0, 256, 0),
            (0, 0, 0, 256),
        ],
    )
    def test_rgbwcolor_to_knx_limits(
        self, red: int, green: int, blue: int, white: int
    ) -> None:
        """Test initialization of DPTColorRGBW with wrong value."""
        value = RGBWColor(red=red, green=green, blue=blue, white=white)
        with pytest.raises(ConversionError):
            DPTColorRGBW.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            (0xFF, 0x4E, 0x12),
            1,
            ((0x00, 0xFF, 0x4E), 0x12),
            ((0xFF, 0x4E), (0x12, 0x00)),
            ((0, 0), "a"),
            ((0, 0), 0.4),
            RGBWColor(red=0, green=0, blue=0, white="a"),
            RGBWColor(red=4, green=4, blue="a", white=4),
            RGBWColor(red="a", green=0, blue=0, white=1),
        ],
    )
    def test_rgbwcolor_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTColorRGBW parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTColorRGBW.to_knx(value)

    def test_rgbwcolor_wrong_value_from_knx(self) -> None:
        """Test DPTColorRGBW parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorRGBW.from_knx(DPTArray((0xFF, 0x4E, 0x12)))


class TestXYYColor:
    """Test XYYColor class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"x_axis": 0.1, "y_axis": 0.2, "brightness": 128},
                XYYColor((0.1, 0.2), 128),
            ),
            (
                {"x_axis": 0.5, "y_axis": 0.5, "brightness": 255},
                XYYColor((0.5, 0.5), 255),
            ),
            (
                {"x_axis": 0.9, "y_axis": 0.8},
                XYYColor((0.9, 0.8)),
            ),
            (
                {"brightness": 50},
                XYYColor(None, 50),
            ),
            (
                {},
                XYYColor(),
            ),
            (
                {"x_axis": None, "y_axis": None, "brightness": 255},
                XYYColor(None, 255),
            ),
            (
                {"x_axis": 0.5, "y_axis": 0.5, "brightness": None},
                XYYColor((0.5, 0.5), None),
            ),
            (
                {"x_axis": None, "brightness": 255},
                XYYColor(None, 255),
            ),
            (
                {"y_axis": None, "brightness": 255},
                XYYColor(None, 255),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: XYYColor) -> None:
        """Test from_dict and as_dict methods."""
        test_value = XYYColor.from_dict(data)
        assert test_value == value
        # fields default to `None`
        default_dict = {"x_axis": None, "y_axis": None, "brightness": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            # incomplete data
            {"x_axis": 0.1},
            {"y_axis": 0.1},
            {"x_axis": 0.1, "brightness": 128},
            {"y_axis": 0.1, "brightness": 128},
            # invalid data
            {"x_axis": "a", "y_axis": 0.1, "brightness": 128},
            {"x_axis": 0.1, "y_axis": "a", "brightness": 128},
            {"x_axis": 0.1, "y_axis": 0.1, "brightness": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            XYYColor.from_dict(data)

    def test_merge(self) -> None:
        """Test merging two XYYColor objects."""
        color1 = XYYColor((1, 1), None)
        color2 = XYYColor(None, 2)
        color3 = XYYColor((3, 3), 3)
        assert color1 | color2 == XYYColor((1, 1), 2)
        assert color2 | color1 == XYYColor((1, 1), 2)
        assert color1 | color3 == XYYColor((3, 3), 3)
        assert color3 | color1 == XYYColor((1, 1), 3)
        assert color2 | color3 == XYYColor((3, 3), 3)
        assert color3 | color2 == XYYColor((3, 3), 2)


class TestDPTColorXYY:
    """Test class for KNX xyY-color objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (XYYColor((0, 0), 0), (0x00, 0x00, 0x00, 0x00, 0x00, 0x03)),  # min values
            (XYYColor((1, 1), 255), (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03)),  # max values
            (XYYColor(None, 0), (0x00, 0x00, 0x00, 0x00, 0x00, 0x01)),  # color None
            (XYYColor((0, 0), None), (0x00, 0x00, 0x00, 0x00, 0x00, 0x02)),
            (XYYColor(None, None), (0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            (XYYColor((0.2, 0.2), 128), (0x33, 0x33, 0x33, 0x33, 0x80, 0x03)),
            (XYYColor((0.8, 0.8), 204), (0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0x03)),
        ],
    )
    def test_xyycolor_value(self, value: XYYColor, raw: tuple[int]) -> None:
        """Test DPTColorXYY parsing and streaming."""
        knx_value = DPTColorXYY.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorXYY.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                {"x_axis": 0.2, "y_axis": 0.2, "brightness": 128},
                (0x33, 0x33, 0x33, 0x33, 0x80, 0x03),
            ),
            (
                {"x_axis": 0.8, "y_axis": 0.8},
                (0xCC, 0xCC, 0xCC, 0xCC, 0x00, 0x02),
            ),
        ],
    )
    def test_xyycolor_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int]
    ) -> None:
        """Test DPTColorXYY parsing from a dict."""
        knx_value = DPTColorXYY.to_knx(value)
        assert knx_value == DPTArray(raw)

    @pytest.mark.parametrize(
        ("color", "brightness"),
        [
            ((-0.1, 0), 0),
            ((0, -0.1), 0),
            ((0, 0), -1),
            ((1.1, 0), 0),
            ((0, 1.1), 0),
            ((0, 0), 256),
        ],
    )
    def test_xyycolor_to_knx_limits(
        self, color: tuple[float, float], brightness: int
    ) -> None:
        """Test initialization of DPTColorXYY with wrong value."""
        value = XYYColor(color=color, brightness=brightness)
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            (0xFF, 0x4E, 0x12),
            1,
            ((0x00, 0xFF, 0x4E), 0x12),
            ((0xFF, 0x4E), (0x12, 0x00)),
            ((0, 0), "a"),
            ((0, 0), 0.4),
            XYYColor(color=(0, 0), brightness="a"),
            XYYColor(color=4, brightness=4),
            XYYColor(color=("a", 0), brightness=1),
        ],
    )
    def test_xyycolor_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTColorXYY parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx(value)

    def test_xyycolor_wrong_value_from_knx(self) -> None:
        """Test DPTColorXYY parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorXYY.from_knx(DPTArray((0xFF, 0x4E, 0x12)))
