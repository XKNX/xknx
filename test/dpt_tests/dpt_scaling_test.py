"""Unit test for KNX DPT 5.001 and 5.003 value."""
import pytest

from xknx.dpt import DPTAngle, DPTArray, DPTScaling
from xknx.exceptions import ConversionError


class TestDPTScaling:
    """Test class for KNX scaling value."""

    def test_value_30_pct(self):
        """Test parsing and streaming of DPTScaling 30%."""
        assert DPTScaling.to_knx(30) == DPTArray((0x4C,))
        assert DPTScaling.from_knx((0x4C,)) == 30

    def test_value_99_pct(self):
        """Test parsing and streaming of DPTScaling 99%."""
        assert DPTScaling.to_knx(99) == DPTArray((0xFC,))
        assert DPTScaling.from_knx((0xFC,)) == 99

    def test_value_max(self):
        """Test parsing and streaming of DPTScaling 100%."""
        assert DPTScaling.to_knx(100) == DPTArray((0xFF,))
        assert DPTScaling.from_knx((0xFF,)) == 100

    def test_value_min(self):
        """Test parsing and streaming of DPTScaling 0."""
        assert DPTScaling.to_knx(0) == DPTArray((0x00,))
        assert DPTScaling.from_knx((0x00,)) == 0

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTScaling with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTScaling.to_knx(-1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTScaling with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTScaling.to_knx(101)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTScaling with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPTScaling.to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTScaling with wrong value (3 byte array)."""
        with pytest.raises(ConversionError):
            DPTScaling.from_knx((0x01, 0x02, 0x03))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTScaling with value which exceeds limits."""
        with pytest.raises(ConversionError):
            DPTScaling.from_knx((0x256,))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTScaling with wrong value (array containing string)."""
        with pytest.raises(ConversionError):
            DPTScaling.from_knx("0x23")


class TestDPTAngle:
    """Test class for KNX scaling value."""

    def test_value_30_deg(self):
        """Test parsing and streaming of DPTAngle 30°."""
        assert DPTAngle.to_knx(30) == DPTArray((0x15,))
        assert DPTAngle.from_knx((0x15,)) == 30

    def test_value_270_deg(self):
        """Test parsing and streaming of DPTAngle 270°."""
        assert DPTAngle.to_knx(270) == DPTArray((0xBF,))
        assert DPTAngle.from_knx((0xBF,)) == 270

    def test_value_max(self):
        """Test parsing and streaming of DPTAngle 360°."""
        assert DPTAngle.to_knx(360) == DPTArray((0xFF,))
        assert DPTAngle.from_knx((0xFF,)) == 360

    def test_value_min(self):
        """Test parsing and streaming of DPTAngle 0°."""
        assert DPTAngle.to_knx(0) == DPTArray((0x00,))
        assert DPTAngle.from_knx((0x00,)) == 0

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTAngle with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTAngle.to_knx(-1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTAngle with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTAngle.to_knx(361)
