"""Unit test for RemoteValueDateTime objects."""
import time

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueDateTime


class TestRemoteValueDateTime:
    """Test class for RemoteValueDateTime objects."""

    def test_init_raises_keyerror(self):
        """Test init raises KeyError if not supported."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueDateTime(xknx, value_type="trees_are_important")

    def test_from_knx(self):
        """Test parsing of RV with datetime object."""
        xknx = XKNX()
        rv_datetime = RemoteValueDateTime(xknx, value_type="datetime")
        assert rv_datetime.from_knx(
            DPTArray((0x75, 0x0B, 0x1C, 0x17, 0x07, 0x18, 0x20, 0x80))
        ) == time.strptime("2017-11-28 23:7:24", "%Y-%m-%d %H:%M:%S")

    def test_to_knx(self):
        """Testing date time object."""
        xknx = XKNX()
        rv_datetime = RemoteValueDateTime(xknx, value_type="datetime")
        array = rv_datetime.to_knx(
            time.strptime("2017-11-28 23:7:24", "%Y-%m-%d %H:%M:%S")
        )
        assert array.value == (0x75, 0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80)

    def test_payload_invalid(self):
        """Testing KNX/Byte representation of DPTDateTime object."""
        xknx = XKNX()
        rv_datetime = RemoteValueDateTime(xknx, value_type="datetime")
        with pytest.raises(CouldNotParseTelegram):
            rv_datetime.from_knx(DPTArray((0x0B, 0x1C, 0x57, 0x07, 0x18, 0x20, 0x80)))
