"""Unit test for KNX datetime objects."""
import time

import pytest

from xknx.dpt import DPTArray, DPTDateTime
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTDateTime:
    """Test class for KNX datetime objects."""

    #
    # TEST CURRENT DATE
    #
    def test_from_knx(self):
        """Test parsing of DPTDateTime object from binary values. Example 1."""
        assert DPTDateTime.from_knx(
            DPTArray((0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x20, 0x80))
        ) == time.strptime("2017-11-28 23:7:24", "%Y-%m-%d %H:%M:%S")

    def test_to_knx(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        raw = DPTDateTime.to_knx(
            time.strptime("2017-11-28 23:7:24", "%Y-%m-%d %H:%M:%S")
        )
        assert raw == DPTArray((0x75, 0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80))

    #
    # TEST EARLIEST DATE POSSIBLE
    #
    def test_from_knx_date_in_past(self):
        """Test parsing of DPTDateTime object from binary values. Example 1."""
        assert DPTDateTime.from_knx(
            DPTArray((0x00, 0x1, 0x1, 0x20, 0x00, 0x00, 0x00, 0x00))
        ) == time.strptime("1900 1 1 0 0 0", "%Y %m %d %H %M %S")

    def test_to_knx_date_in_past(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        raw = DPTDateTime.to_knx(
            time.strptime("1900-1-1 1 0:0:0", "%Y-%m-%d %w %H:%M:%S")
        )
        assert raw == DPTArray((0x00, 0x1, 0x1, 0x20, 0x00, 0x00, 0x20, 0x80))

    #
    # TEST LATEST DATE IN THE FUTURE
    #
    def test_from_knx_date_in_future(self):
        """Test parsing of DPTDateTime object from binary values. Example 1."""
        assert DPTDateTime.from_knx(
            DPTArray((0xFF, 0x0C, 0x1F, 0xF7, 0x3B, 0x3B, 0x20, 0x80))
        ) == time.strptime("2155-12-31 0 23:59:59", "%Y-%m-%d %w %H:%M:%S")

    def test_to_knx_date_in_future(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        raw = DPTDateTime.to_knx(
            time.strptime("2155-12-31 0 23:59:59", "%Y-%m-%d %w %H:%M:%S")
        )
        assert raw == DPTArray((0xFF, 0x0C, 0x1F, 0xF7, 0x3B, 0x3B, 0x20, 0x80))

    #
    # TEST WRONG KNX
    #
    def test_from_knx_wrong_size(self):
        """Test parsing DPTDateTime from KNX with wrong binary values (wrong size)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDateTime.from_knx(DPTArray((0xF8, 0x23)))

    def test_from_knx_wrong_bytes(self):
        """Test parsing DPTDateTime from KNX with wrong binary values (wrong bytes)."""
        with pytest.raises(ConversionError):
            # (second byte exceeds value...)
            DPTDateTime.from_knx(
                DPTArray((0xFF, 0x0D, 0x1F, 0xF7, 0x3B, 0x3B, 0x00, 0x00))
            )

    #
    # TEST WRONG PARAMETER
    #
    def test_to_knx_wrong_parameter(self):
        """Test parsing from DPTDateTime object from wrong string value."""
        with pytest.raises(ConversionError):
            DPTDateTime.to_knx("hello")
