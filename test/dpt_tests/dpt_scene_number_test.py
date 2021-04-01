"""Unit test for KNX scene number."""
import pytest
from xknx.dpt import DPTSceneNumber
from xknx.exceptions import ConversionError


class TestDPTSceneNumber:
    """Test class for KNX scaling value."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_value_50(self):
        """Test parsing and streaming of DPTSceneNumber 50."""
        assert DPTSceneNumber().to_knx(50) == (0x31,)
        assert DPTSceneNumber().from_knx((0x31,)) == 50

    def test_value_max(self):
        """Test parsing and streaming of DPTSceneNumber 64."""
        assert DPTSceneNumber().to_knx(64) == (0x3F,)
        assert DPTSceneNumber().from_knx((0x3F,)) == 64

    def test_value_min(self):
        """Test parsing and streaming of DPTSceneNumber 0."""
        assert DPTSceneNumber().to_knx(1) == (0x00,)
        assert DPTSceneNumber().from_knx((0x00,)) == 1

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTSceneNumber with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber().to_knx(DPTSceneNumber.value_min - 1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTSceneNumber with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber().to_knx(DPTSceneNumber.value_max + 1)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTSceneNumber with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber().to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTSceneNumber with wrong value (3 byte array)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber().from_knx((0x01, 0x02, 0x03))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTSceneNumber with value which exceeds limits."""
        with pytest.raises(ConversionError):
            DPTSceneNumber().from_knx((0x64,))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTSceneNumber with wrong value (array containing string)."""
        with pytest.raises(ConversionError):
            DPTSceneNumber().from_knx("0x23")
