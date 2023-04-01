"""Unit test for KNX 2 byte objects."""
import pytest

from xknx.dpt import DPTArray, DPTUElCurrentmA
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPT2byte:
    """Test class for KNX 2 byte objects."""

    #
    # DPTUElCurrentmA
    #
    def test_current_settings(self):
        """Test members of DPTUElCurrentmA."""
        assert DPTUElCurrentmA.value_min == 0
        assert DPTUElCurrentmA.value_max == 65535
        assert DPTUElCurrentmA.unit == "mA"
        assert DPTUElCurrentmA.resolution == 1

    def test_current_assert_min_exceeded(self):
        """Test initialization of DPTUElCurrentmA with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPTUElCurrentmA.to_knx(-1)

    def test_current_to_knx_exceed_limits(self):
        """Test initialization of DPTUElCurrentmA with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPTUElCurrentmA.to_knx(65536)

    def test_current_value_max_value(self):
        """Test DPTUElCurrentmA parsing and streaming."""
        assert DPTUElCurrentmA.to_knx(65535) == DPTArray((0xFF, 0xFF))
        assert DPTUElCurrentmA.from_knx(DPTArray((0xFF, 0xFF))) == 65535

    def test_current_value_min_value(self):
        """Test DPTUElCurrentmA parsing and streaming with null values."""
        assert DPTUElCurrentmA.to_knx(0) == DPTArray((0x00, 0x00))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x00, 0x00))) == 0

    def test_current_value_38(self):
        """Test DPTUElCurrentmA parsing and streaming 38mA."""
        assert DPTUElCurrentmA.to_knx(38) == DPTArray((0x00, 0x26))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x00, 0x26))) == 38

    def test_current_value_78(self):
        """Test DPTUElCurrentmA parsing and streaming 78mA."""
        assert DPTUElCurrentmA.to_knx(78) == DPTArray((0x00, 0x4E))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x00, 0x4E))) == 78

    def test_current_value_1234(self):
        """Test DPTUElCurrentmA parsing and streaming 4660mA."""
        assert DPTUElCurrentmA.to_knx(4660) == DPTArray((0x12, 0x34))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x12, 0x34))) == 4660

    def test_current_wrong_value_from_knx(self):
        """Test DPTUElCurrentmA parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTUElCurrentmA.from_knx(DPTArray((0xFF, 0x4E, 0x12)))
