"""Unit test for KNX color objects."""

import pytest

from xknx.dpt.dpt_color import DPTArray, DPTColorXYY, XYYColor
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTColorXYY:
    """Test class for KNX xyY-color objects."""

    @pytest.mark.parametrize(
        ("color", "brightness", "raw"),
        [
            ((0, 0), 0, (0x00, 0x00, 0x00, 0x00, 0x00, 0x03)),  # min values
            ((1, 1), 255, (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x03)),  # max values
            (None, 0, (0x00, 0x00, 0x00, 0x00, 0x00, 0x01)),  # color None
            ((0, 0), None, (0x00, 0x00, 0x00, 0x00, 0x00, 0x02)),  # brightness None
            (
                None,
                None,
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),  # color and brightness None
            ((0.2, 0.2), 128, (0x33, 0x33, 0x33, 0x33, 0x80, 0x03)),
            ((0.8, 0.8), 204, (0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0x03)),
        ],
    )
    def test_xyycolor_value(self, color, brightness, raw):
        """Test DPTColorXYY parsing and streaming."""
        value = XYYColor(color=color, brightness=brightness)
        knx_value = DPTColorXYY.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTColorXYY.from_knx(knx_value) == value

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
