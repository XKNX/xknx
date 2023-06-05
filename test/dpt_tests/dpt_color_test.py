"""Unit test for KNX color objects."""

import pytest

from xknx.dpt.dpt_color import DPTArray, DPTColorXYY, XYYColor
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTColorXYY:
    """Test class for KNX xyY-color objects."""

    def test_xyycolor_assert_min_exceeded(self):
        """Test initialization of DPTColorXYY with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx({"x_axis": -0.1, "y_axis": 0, "brightness": 0})
            DPTColorXYY.to_knx({"x_axis": 0, "y_axis": -0.1, "brightness": 0})
            DPTColorXYY.to_knx({"x_axis": 0, "y_axis": 0, "brightness": -1})

    def test_xyycolor_to_knx_exceed_limits(self):
        """Test initialization of DPTColorXYY with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx({"x_axis": 1.1, "y_axis": 0, "brightness": 0})
            DPTColorXYY.to_knx({"x_axis": 0, "y_axis": 1.1, "brightness": 0})
            DPTColorXYY.to_knx({"x_axis": 0, "y_axis": 0, "brightness": 256})

    def test_xyycolor_value_max_value(self):
        """Test DPTColorXYY parsing and streaming."""
        assert DPTColorXYY.to_knx(
            {"x_axis": 1, "y_axis": 1, "brightness": 255}
        ) == DPTArray((0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03))
        assert DPTColorXYY.from_knx(DPTArray((0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03))) == {
            "x_axis": 1,
            "y_axis": 1,
            "brightness": 255,
        }

    def test_xyycolor_value_min_value(self):
        """Test DPTColorXYY parsing and streaming with null values."""
        assert DPTColorXYY.to_knx(
            {"x_axis": 0, "y_axis": 0, "brightness": 0}
        ) == DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x03))
        assert DPTColorXYY.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x03))) == {
            "x_axis": 0,
            "y_axis": 0,
            "brightness": 0,
        }

    def test_xyycolor_value_none_value(self):
        """Test DPTColorXYY parsing and streaming with null values."""
        assert DPTColorXYY.to_knx({"brightness": 0}) == DPTArray(
            (0x00, 0x00, 0x00, 0x00, 0x00, 0x01)
        )
        assert DPTColorXYY.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x01))) == {
            "x_axis": None,
            "y_axis": None,
            "brightness": 0,
        }

        assert DPTColorXYY.to_knx(
            {"x_axis": 0, "y_axis": 0, "brightness": None}
        ) == DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x02))
        assert DPTColorXYY.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x02))) == {
            "x_axis": 0,
            "y_axis": 0,
            "brightness": None,
        }

        assert DPTColorXYY.to_knx({}) == DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00))
        assert DPTColorXYY.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00))) == {
            "x_axis": None,
            "y_axis": None,
            "brightness": None,
        }

    def test_xyycolor_value(self):
        """Test DPTColorXYY parsing and streaming with valid value."""
        assert DPTColorXYY.to_knx(
            {"x_axis": 0.2, "y_axis": 0.2, "brightness": 128}
        ) == DPTArray((0x33, 0x33, 0x33, 0x33, 0x80, 0x03))
        assert DPTColorXYY.from_knx(DPTArray((0x33, 0x33, 0x33, 0x33, 0x80, 0x03))) == {
            "x_axis": 0.2,
            "y_axis": 0.2,
            "brightness": 128,
        }
        assert DPTColorXYY.to_knx(
            XYYColor(x_axis=0.8, y_axis=0.8, brightness=204)
        ) == DPTArray((0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0x03))
        assert DPTColorXYY.from_knx(
            DPTArray((0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0x03))
        ) == XYYColor(x_axis=0.8, y_axis=0.8, brightness=204)

    def test_xyycolor_wrong_value_to_knx(self):
        """Test DPTColorXYY parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx(None)
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx(1)
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx((0xFF, 0x4E, 0x12))
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx({"x_axis": "a", "y_axis": "b", "brightness": 256})
        with pytest.raises(ConversionError):
            DPTColorXYY.to_knx({"x_axis": 1, "y_axis": 1, "brightness": "c"})

    def test_xyycolor_wrong_value_from_knx(self):
        """Test DPTColorXYY parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTColorXYY.from_knx(DPTArray((0xFF, 0x4E, 0x12)))
