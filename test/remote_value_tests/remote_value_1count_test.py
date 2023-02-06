"""Unit test for RemoteValue1Count objects."""
from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.remote_value import RemoteValue1Count
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValue1Count:
    """Test class for RemoteValue1Count objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx)
        assert remote_value.to_knx(100) == DPTArray((0x64,))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx)
        assert remote_value.from_knx(DPTArray((0x64,))) == 100

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.set(100)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64,))),
        )
        await remote_value.set(101)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x65,))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64,))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == 100

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
