"""Unit test for RemoteValueColorRGBW objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueColorRGBW
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueColorRGBW:
    """Test class for RemoteValueColorRGBW objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        input_list = [100, 101, 102, 127]
        input_tuple = (100, 101, 102, 127)
        expected = DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x0F))
        assert remote_value.to_knx(input_tuple) == expected
        assert remote_value.to_knx(input_list) == expected
        assert remote_value.to_knx((*input_tuple, 15)) == expected
        assert remote_value.to_knx([*input_list, 15]) == expected
        assert remote_value.to_knx((*input_tuple, 0, 15)) == expected
        assert remote_value.to_knx([*input_list, 0, 15]) == expected

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x00))
        ) == (0, 0, 0, 0)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x0F))
        ) == (100, 101, 102, 127)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x00))
        ) == (100, 101, 102, 127)
        assert remote_value.from_knx(
            DPTArray((0xFF, 0x65, 0x66, 0xFF, 0x00, 0x09))
        ) == (255, 101, 102, 255)
        assert remote_value.from_knx(
            DPTArray((0x64, 0x65, 0x66, 0x7F, 0x00, 0x01))
        ) == (255, 101, 102, 127)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx((101, 102, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx((0, 0, 15, 101, 102, 103, 104))
        with pytest.raises(ConversionError):
            remote_value.to_knx((256, 101, 102, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, 256, 102, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, 101, 256, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, 101, 102, 256))
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, -101, 102, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx(("100", 101, 102, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx("100, 101, 102, 103")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.set((100, 101, 102, 103))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66, 0x67, 0x00, 0x0F))),
        )
        await remote_value.set((100, 101, 104, 105))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x68, 0x69, 0x00, 0x0F))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66, 0x67, 0x00, 0x0F))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == (100, 101, 102, 103)

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66))),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(
                DPTArray((0x00, 0x00, 0x0F, 0x64, 0x65, 0x66, 0x67))
            ),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
