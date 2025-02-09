"""Unit test for RemoteValueColorRGB objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, RGBColor
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueColorRGB
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueColorRGB:
    """Test class for RemoteValueColorRGB objects."""

    def test_to_knx(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx)
        assert remote_value.to_knx(RGBColor(100, 101, 102)) == DPTArray(
            (0x64, 0x65, 0x66)
        )
        assert remote_value.to_knx(RGBColor(100, 101, 102)) == DPTArray(
            (0x64, 0x65, 0x66)
        )

    def test_from_knx(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx)
        assert remote_value.from_knx(DPTArray((0x64, 0x65, 0x66))) == RGBColor(
            100, 101, 102
        )

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(RGBColor(100, 101, 256))
        with pytest.raises(ConversionError):
            remote_value.to_knx(RGBColor(100, -1, 102))
        with pytest.raises(ConversionError):
            remote_value.to_knx(RGBColor("100", 101, 102))

    async def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx, group_address=GroupAddress("1/2/3"))
        remote_value.set(RGBColor(100, 101, 102))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66))),
        )
        remote_value.set(RGBColor(100, 101, 104))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x68))),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66))),
        )
        remote_value.process(telegram)
        assert remote_value.value == RGBColor(100, 101, 102)

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66, 0x67))),
        )
        assert remote_value.process(telegram) is False

        assert remote_value.value is None
