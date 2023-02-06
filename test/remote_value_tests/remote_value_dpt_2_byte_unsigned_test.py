"""Unit test for RemoteValueDpt2ByteUnsigned objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueDpt2ByteUnsigned
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueDptValue2Ucount:
    """Test class for RemoteValueDpt2ByteUnsigned objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueDpt2ByteUnsigned(xknx)
        assert remote_value.to_knx(2571) == DPTArray((0x0A, 0x0B))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueDpt2ByteUnsigned(xknx)
        assert remote_value.from_knx(DPTArray((0x0A, 0x0B))) == 2571

    def test_to_knx_error(self):
        """Test to_knx function with wrong parameters."""
        xknx = XKNX()
        remote_value = RemoteValueDpt2ByteUnsigned(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(65536)
        with pytest.raises(ConversionError):
            remote_value.to_knx("a")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueDpt2ByteUnsigned(
            xknx, group_address=GroupAddress("1/2/3")
        )
        await remote_value.set(2571)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A, 0x0B))),
        )
        await remote_value.set(5500)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x15, 0x7C))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueDpt2ByteUnsigned(
            xknx, group_address=GroupAddress("1/2/3")
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A, 0x0B))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == 2571

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueDpt2ByteUnsigned(
            xknx, group_address=GroupAddress("1/2/3")
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64,))),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x53, 0x42))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
