"""Unit test for KNX DPT 1 byte relative value  objects."""
import pytest

from xknx.dpt import DPTPercentV8, DPTSignedRelativeValue, DPTValue1Count
from xknx.exceptions import ConversionError


class TestDPTRelativeValue:
    """Test class for KNX DPT Relative Value."""

    def test_from_knx_positive(self):
        """Test positive value from KNX."""
        assert DPTSignedRelativeValue.from_knx((0x00,)) == 0
        assert DPTSignedRelativeValue.from_knx((0x01,)) == 1
        assert DPTSignedRelativeValue.from_knx((0x02,)) == 2
        assert DPTSignedRelativeValue.from_knx((0x64,)) == 100
        assert DPTSignedRelativeValue.from_knx((0x7F,)) == 127

    def test_from_knx_negative(self):
        """Test negative value from KNX."""
        assert DPTSignedRelativeValue.from_knx((0x80,)) == -128
        assert DPTSignedRelativeValue.from_knx((0x9C,)) == -100
        assert DPTSignedRelativeValue.from_knx((0xFE,)) == -2
        assert DPTSignedRelativeValue.from_knx((0xFF,)) == -1

    def test_to_knx_positive(self):
        """Test positive value to KNX."""
        assert DPTSignedRelativeValue.to_knx(0) == (0x00,)
        assert DPTSignedRelativeValue.to_knx(1) == (0x01,)
        assert DPTSignedRelativeValue.to_knx(2) == (0x02,)
        assert DPTSignedRelativeValue.to_knx(100) == (0x64,)
        assert DPTSignedRelativeValue.to_knx(127) == (0x7F,)

    def test_to_knx_negative(self):
        """Test negative value to KNX."""
        assert DPTSignedRelativeValue.to_knx(-128) == (0x80,)
        assert DPTSignedRelativeValue.to_knx(-100) == (0x9C,)
        assert DPTSignedRelativeValue.to_knx(-2) == (0xFE,)
        assert DPTSignedRelativeValue.to_knx(-1) == (0xFF,)

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
        assert DPTSignedRelativeValue.unit == ""
        assert DPTPercentV8.unit == "%"
        assert DPTValue1Count.unit == "counter pulses"
