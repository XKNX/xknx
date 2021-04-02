"""Unit test for RemoteValueSceneNumber objects."""
import pytest
from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueSceneNumber
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


@pytest.mark.asyncio
class TestRemoteValueSceneNumber:
    """Test class for RemoteValueSceneNumber objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSceneNumber(xknx)
        assert remote_value.to_knx(11) == DPTArray((0x0A,))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSceneNumber(xknx)
        assert remote_value.from_knx(DPTArray((0x0A,))) == 11

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueSceneNumber(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(100)
        with pytest.raises(ConversionError):
            remote_value.to_knx("100")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueSceneNumber(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.set(11)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A,))),
        )
        await remote_value.set(12)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0B,))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSceneNumber(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A,))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == 11

    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSceneNumber(xknx, group_address=GroupAddress("1/2/3"))
        with pytest.raises(CouldNotParseTelegram):
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTBinary(1)),
            )
            await remote_value.process(telegram)
        with pytest.raises(CouldNotParseTelegram):
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(
                    DPTArray(
                        (
                            0x64,
                            0x65,
                        )
                    )
                ),
            )
            await remote_value.process(telegram)
