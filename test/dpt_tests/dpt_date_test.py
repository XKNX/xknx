"""Unit test for KNX date objects."""
import time

import pytest

from xknx.dpt import DPTArray, DPTDate
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTDate:
    """Test class for KNX date objects."""

    def test_from_knx(self):
        """Test parsing of DPTDate object from binary values. Example 1."""
        assert DPTDate.from_knx(DPTArray((0x04, 0x01, 0x02))) == time.strptime(
            "2002-01-04", "%Y-%m-%d"
        )

    def test_from_knx_old_date(self):
        """Test parsing of DPTDate object from binary values. Example 2."""
        assert DPTDate.from_knx(DPTArray((0x1F, 0x01, 0x5A))) == time.strptime(
            "1990-01-31", "%Y-%m-%d"
        )

    def test_from_knx_future_date(self):
        """Test parsing of DPTDate object from binary values. Example 3."""
        assert DPTDate.from_knx(DPTArray((0x04, 0x0C, 0x59))) == time.strptime(
            "2089-12-4", "%Y-%m-%d"
        )

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTDate object. Example 1."""
        raw = DPTDate.to_knx(time.strptime("2002-1-04", "%Y-%m-%d"))
        assert raw == DPTArray((0x04, 0x01, 0x02))

    def test_to_knx_old_date(self):
        """Testing KNX/Byte representation of DPTDate object. Example 2."""
        raw = DPTDate.to_knx(time.strptime("1990-01-31", "%Y-%m-%d"))
        assert raw == DPTArray((0x1F, 0x01, 0x5A))

    def test_to_knx_future_date(self):
        """Testing KNX/Byte representation of DPTDate object. Example 3."""
        raw = DPTDate.to_knx(time.strptime("2089-12-04", "%Y-%m-%d"))
        assert raw == DPTArray((0x04, 0x0C, 0x59))

    def test_from_knx_wrong_parameter(self):
        """Test parsing from DPTDate object from wrong binary values."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDate.from_knx(DPTArray((0xF8, 0x23)))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTDate object from wrong string value."""
        with pytest.raises(ConversionError):
            DPTDate.to_knx("hello")

    def test_from_knx_wrong_range_month(self):
        """Test Exception when parsing DPTDAte from KNX with wrong month."""
        with pytest.raises(ConversionError):
            DPTDate.from_knx(DPTArray((0x04, 0x00, 0x59)))

    def test_from_knx_wrong_range_year(self):
        """Test Exception when parsing DPTDate from KNX with wrong year."""
        with pytest.raises(ConversionError):
            DPTDate.from_knx(DPTArray((0x04, 0x01, 0x64)))
