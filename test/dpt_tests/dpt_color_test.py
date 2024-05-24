"""Unit test for KNX color objects."""

import pytest

from xknx.dpt.dpt_color import DPTArray, DPTColorXYY, XYYColor
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestXYYColor:
    """Test XYYColor class."""

    @pytest.mark.parametrize(
        "data",
        [
            {"x_axis": 0.1, "y_axis": 0.2, "brightness": 128},
            {"x_axis": 0.5, "y_axis": 0.5, "brightness": 255},
            {"x_axis": 0.9, "y_axis": 0.8},
            {"brightness": 50},
            {},
        ],
    )
    def test_dict(self, data):
        """Test from_dict and as_dict methods."""
        value = XYYColor.from_dict(data)
        assert value
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
    def test_dict_invalid(self, data):
        """Test from_dict and as_dict methods."""
        with pytest.raises(ValueError):
            XYYColor.from_dict(data)


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
    def test_xyycolor_value(self, value, raw):
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
    def test_xyycolor_to_knx_from_dict(self, value, raw):
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
    def test_xyycolor_to_knx_limits(self, color, brightness):
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
    def test_xyycolor_wrong_value_to_knx(self, value):
        """Test DPTColorXYY parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx(value)

    def test_xyycolor_wrong_value_from_knx(self):
        """Test DPTColorXYY parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorXYY.from_knx(DPTArray((0xFF, 0x4E, 0x12)))
