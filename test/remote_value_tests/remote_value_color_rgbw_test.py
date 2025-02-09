"""Unit test for RemoteValueColorRGBW objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, RGBWColor
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueColorRGBW
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueColorRGBW:
    """Test class for RemoteValueColorRGBW objects."""

    def test_to_knx(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        input_value = RGBWColor(100, 101, 102, 127)
        expected = DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x0F))
        assert remote_value.to_knx(input_value) == expected

    def test_from_knx(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x00))
        ) == RGBWColor(None, None, None, None)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x0F))
        ) == RGBWColor(100, 101, 102, 127)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x00))
        ) == RGBWColor(100, 101, 102, 127)
        assert remote_value.from_knx(
            DPTArray((0xFF, 0x65, 0x66, 0xFF, 0x00, 0x09))
        ) == RGBWColor(255, 101, 102, 255)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x01))
        ) == RGBWColor(255, 101, 102, 127)

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx((101, 102, 103, 104))

    async def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx, group_address=GroupAddress("1/2/3"))
        remote_value.set(RGBWColor(100, 101, 102, 103))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66, 0x67, 0x00, 0x0F))),
        )
        remote_value.set(RGBWColor(100, 101, 104, 105))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x68, 0x69, 0x00, 0x0F))),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66, 0x67, 0x00, 0x0F))),
        )
        remote_value.process(telegram)
        assert remote_value.value == RGBWColor(100, 101, 102, 103)

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66))),
        )
        assert remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(
                DPTArray((0x00, 0x00, 0x0F, 0x64, 0x65, 0x66, 0x67))
            ),
        )
        assert remote_value.process(telegram) is False

        assert remote_value.value is None
