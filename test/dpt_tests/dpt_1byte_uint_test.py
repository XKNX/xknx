"""Unit test for KNX DPT 5.010 value."""
import pytest

from xknx.dpt import DPTArray, DPTTariff, DPTValue1Ucount
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTValue1Ucount:
    """Test class for KNX 8-bit unsigned value."""

    def test_value_50(self):
        """Test parsing and streaming of DPTValue1Ucount 50."""
        assert DPTValue1Ucount.to_knx(50) == DPTArray(0x32)
        assert DPTValue1Ucount.from_knx(DPTArray((0x32,))) == 50

    def test_value_max(self):
        """Test parsing and streaming of DPTValue1Ucount 255."""
        assert DPTValue1Ucount.to_knx(255) == DPTArray(0xFF)
        assert DPTValue1Ucount.from_knx(DPTArray((0xFF,))) == 255

    def test_value_min(self):
        """Test parsing and streaming of DPTValue1Ucount 0."""
        assert DPTValue1Ucount.to_knx(0) == DPTArray(0x00)
        assert DPTValue1Ucount.from_knx(DPTArray((0x00,))) == 0

    def test_to_knx_min_exceeded(self):
        """Test parsing of DPTValue1Ucount with wrong value (underflow)."""
        with pytest.raises(ConversionError):
            DPTValue1Ucount.to_knx(DPTValue1Ucount.value_min - 1)

    def test_to_knx_max_exceeded(self):
        """Test parsing of DPTValue1Ucount with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTValue1Ucount.to_knx(DPTValue1Ucount.value_max + 1)

    def test_to_knx_wrong_parameter(self):
        """Test parsing of DPTValue1Ucount with wrong value (string)."""
        with pytest.raises(ConversionError):
            DPTValue1Ucount.to_knx("fnord")

    def test_from_knx_wrong_parameter(self):
        """Test parsing of DPTValue1Ucount with wrong value (3 byte array)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTValue1Ucount.from_knx(DPTArray((0x01, 0x02, 0x03)))

    def test_from_knx_wrong_value(self):
        """Test parsing of DPTValue1Ucount with value which exceeds limits."""
        with pytest.raises(ConversionError):
            DPTValue1Ucount.from_knx(DPTArray((0x256,)))

    def test_from_knx_wrong_parameter2(self):
        """Test parsing of DPTValue1Ucount with wrong value (array containing string)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTValue1Ucount.from_knx("0x23")


class TestDPTTariff:
    """Test class for KNX 8-bit tariff information."""

    def test_from_knx_max_exceeded(self):
        """Test parsing of DPTTariff with wrong value (overflow)."""
        with pytest.raises(ConversionError):
            DPTTariff.from_knx(DPTArray((0xFF,)))
