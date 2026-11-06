"""Unit test for KNX 2 byte objects."""

import pytest

from xknx.dpt import DPTArray, DPTTimePeriod10Msec, DPTUElCurrentmA
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPT2byte:
    """Test class for KNX 2 byte objects."""

    #
    # DPTUElCurrentmA
    #
    def test_current_settings(self) -> None:
        """Test members of DPTUElCurrentmA."""
        assert DPTUElCurrentmA.value_min == 0
        assert DPTUElCurrentmA.value_max == 65535
        assert DPTUElCurrentmA.unit == "mA"
        assert DPTUElCurrentmA.resolution == 1

    def test_current_assert_min_exceeded(self) -> None:
        """Test initialization of DPTUElCurrentmA with wrong value (Underflow)."""
        with pytest.raises(ConversionError):
            DPTUElCurrentmA.to_knx(-1)

    def test_current_to_knx_exceed_limits(self) -> None:
        """Test initialization of DPTUElCurrentmA with wrong value (Overflow)."""
        with pytest.raises(ConversionError):
            DPTUElCurrentmA.to_knx(65536)

    def test_current_value_max_value(self) -> None:
        """Test DPTUElCurrentmA parsing and streaming."""
        assert DPTUElCurrentmA.to_knx(65535) == DPTArray((0xFF, 0xFF))
        assert DPTUElCurrentmA.from_knx(DPTArray((0xFF, 0xFF))) == 65535

    def test_current_value_min_value(self) -> None:
        """Test DPTUElCurrentmA parsing and streaming with null values."""
        assert DPTUElCurrentmA.to_knx(0) == DPTArray((0x00, 0x00))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x00, 0x00))) == 0

    def test_current_value_38(self) -> None:
        """Test DPTUElCurrentmA parsing and streaming 38mA."""
        assert DPTUElCurrentmA.to_knx(38) == DPTArray((0x00, 0x26))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x00, 0x26))) == 38

    def test_current_value_78(self) -> None:
        """Test DPTUElCurrentmA parsing and streaming 78mA."""
        assert DPTUElCurrentmA.to_knx(78) == DPTArray((0x00, 0x4E))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x00, 0x4E))) == 78

    def test_current_value_1234(self) -> None:
        """Test DPTUElCurrentmA parsing and streaming 4660mA."""
        assert DPTUElCurrentmA.to_knx(4660) == DPTArray((0x12, 0x34))
        assert DPTUElCurrentmA.from_knx(DPTArray((0x12, 0x34))) == 4660

    def test_current_wrong_value_from_knx(self) -> None:
        """Test DPTUElCurrentmA parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTUElCurrentmA.from_knx(DPTArray((0xFF, 0x4E, 0x12)))

    def test_to_knx_rounding(self) -> None:
        """Test values are rounded to the resolution instead of floored."""
        assert DPTUElCurrentmA.to_knx(38.6) == DPTArray((0x00, 0x27))
        assert DPTUElCurrentmA.to_knx(38.4) == DPTArray((0x00, 0x26))
        assert DPTTimePeriod10Msec.to_knx(19) == DPTArray((0x00, 0x02))
        assert DPTTimePeriod10Msec.to_knx(14) == DPTArray((0x00, 0x01))
        assert DPTTimePeriod10Msec.to_knx(655_354) == DPTArray((0xFF, 0xFF))
        with pytest.raises(ConversionError):
            DPTTimePeriod10Msec.to_knx(655_356)
