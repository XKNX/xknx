"""Unit test for KNX DPT 1 byte relative value  objects."""
import pytest

from xknx.dpt import DPTArray, DPTPercentV8, DPTSignedRelativeValue, DPTValue1Count
from xknx.exceptions import ConversionError


class TestDPTRelativeValue:
    """Test class for KNX DPT Relative Value."""

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            ((0x00,), 0),
            ((0x01,), 1),
            ((0x02,), 2),
            ((0x64,), 100),
            ((0x7F,), 127),
            ((0x80,), -128),
            ((0x9C,), -100),
            ((0xFE,), -2),
            ((0xFF,), -1),
        ],
    )
    def test_transcoder(self, raw, value):
        """Test value from and to KNX."""
        assert DPTSignedRelativeValue.from_knx(DPTArray(raw)) == value
        assert DPTSignedRelativeValue.to_knx(value) == DPTArray(raw)

    def test_assert_min_exceeded(self):
        """Test initialization with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPTSignedRelativeValue.to_knx(-129)

    def test_assert_max_exceeded(self):
        """Test initialization with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPTSignedRelativeValue.to_knx(128)

    def test_unit(self):
        """Test unit of 1 byte relative value objects."""
        assert DPTSignedRelativeValue.unit is None
        assert DPTPercentV8.unit == "%"
        assert DPTValue1Count.unit == "counter pulses"
