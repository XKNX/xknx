"""Unit test for KNX time objects."""
import time

import pytest

from xknx.dpt import DPTArray, DPTTime
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTTime:
    """Test class for KNX time objects."""

    #
    # TEST NORMAL TIME
    #
    def test_from_knx(self):
        """Test parsing of DPTTime object from binary values. Example 1."""
        assert DPTTime.from_knx(DPTArray((0x4D, 0x17, 0x2A))) == time.strptime(
            "13 23 42 2", "%H %M %S %w"
        )

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTTime object."""
        raw = DPTTime.to_knx(time.strptime("13 23 42 2", "%H %M %S %w"))
        assert raw == DPTArray((0x4D, 0x17, 0x2A))

    #
    # TEST MAXIMUM TIME
    #
    def test_to_knx_max(self):
        """Testing KNX/Byte representation of DPTTime object. Maximum values."""
        raw = DPTTime.to_knx(time.strptime("23 59 59 0", "%H %M %S %w"))
        assert raw == DPTArray((0xF7, 0x3B, 0x3B))

    def test_from_knx_max(self):
        """Test parsing of DPTTime object from binary values. Example 2."""
        assert DPTTime.from_knx(DPTArray((0xF7, 0x3B, 0x3B))) == time.strptime(
            "23 59 59 0", "%H %M %S %w"
        )

    #
    # TEST MINIMUM TIME
    #
    def test_to_knx_min(self):
        """Testing KNX/Byte representation of DPTTime object. Minimum values."""
        raw = DPTTime.to_knx(time.strptime("0 0 0", "%H %M %S"))
        assert raw == DPTArray((0x0, 0x0, 0x0))

    def test_from_knx_min(self):
        """Test parsing of DPTTime object from binary values. Example 3."""
        assert DPTTime.from_knx(DPTArray((0x0, 0x0, 0x0))) == time.strptime(
            "0 0 0", "%H %M %S"
        )

    #
    # TEST INITIALIZATION
    #
    def test_to_knx_default(self):
        """Testing default initialization of DPTTime object."""
        assert DPTTime.to_knx(time.strptime("", "")) == DPTArray((0x0, 0x0, 0x0))

    def test_from_knx_wrong_size(self):
        """Test parsing from DPTTime object from wrong binary values (wrong size)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTTime.from_knx(DPTArray((0xF8, 0x23)))

    def test_from_knx_wrong_bytes(self):
        """Test parsing from DPTTime object from wrong binary values (wrong bytes)."""
        with pytest.raises(ConversionError):
            # this parameter exceeds limit
            DPTTime.from_knx(DPTArray((0xF7, 0x3B, 0x3C)))

    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTTime object from wrong string value."""
        with pytest.raises(ConversionError):
            DPTTime.to_knx("fnord")
