"""Unit test for RemoteValueColorRGB objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueColorRGB
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueColorRGB:
    """Test class for RemoteValueColorRGB objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx)
        assert remote_value.to_knx((100, 101, 102)) == DPTArray((0x64, 0x65, 0x66))
        assert remote_value.to_knx([100, 101, 102]) == DPTArray((0x64, 0x65, 0x66))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx)
        assert remote_value.from_knx(DPTArray((0x64, 0x65, 0x66))) == (100, 101, 102)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, 101, 102, 103))
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, 101, 256))
        with pytest.raises(ConversionError):
            remote_value.to_knx((100, -101, 102))
        with pytest.raises(ConversionError):
            remote_value.to_knx(("100", 101, 102))
        with pytest.raises(ConversionError):
            remote_value.to_knx("100, 101, 102")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.set((100, 101, 102))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66))),
        )
        await remote_value.set((100, 101, 104))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x68))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == (100, 101, 102)

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGB(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65, 0x66, 0x67))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
