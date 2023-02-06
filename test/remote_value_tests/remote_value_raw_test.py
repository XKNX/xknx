"""Unit test for RemoteValueRaw objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueRaw
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueRaw:
    """Test class for RemoteValueRaw objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        rv_0 = RemoteValueRaw(xknx, payload_length=0)
        rv_1 = RemoteValueRaw(xknx, payload_length=1)
        rv_2 = RemoteValueRaw(xknx, payload_length=2)

        assert rv_0.to_knx(1) == DPTBinary(True)
        assert rv_0.to_knx(4) == DPTBinary(4)
        assert rv_1.to_knx(100) == DPTArray((0x64,))
        assert rv_2.to_knx(100) == DPTArray((0x00, 0x64))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        rv_0 = RemoteValueRaw(xknx, payload_length=0)
        rv_1 = RemoteValueRaw(xknx, payload_length=1)
        rv_2 = RemoteValueRaw(xknx, payload_length=2)

        assert rv_0.from_knx(DPTBinary(True)) == 1
        assert rv_0.from_knx(DPTBinary(0x4)) == 4
        assert rv_1.from_knx(DPTArray((0x64,))) == 100
        assert rv_2.from_knx(DPTArray((0x00, 0x64))) == 100

        with pytest.raises(ConversionError):
            assert rv_1.from_knx(DPTArray((256,)))

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        rv_0 = RemoteValueRaw(xknx, payload_length=0, group_address="1/2/3")
        rv_1 = RemoteValueRaw(xknx, payload_length=1, group_address="1/2/3")
        rv_2 = RemoteValueRaw(xknx, payload_length=2, group_address="1/2/3")

        await rv_0.set(0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(False)),
        )
        await rv_0.set(63)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0x3F)),
        )

        await rv_1.set(0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00,))),
        )
        await rv_1.set(63)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x3F,))),
        )

        await rv_2.set(0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00, 0x00))),
        )
        await rv_2.set(63)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00, 0x3F))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        rv_0 = RemoteValueRaw(xknx, payload_length=0, group_address="1/0/0")
        rv_1 = RemoteValueRaw(xknx, payload_length=1, group_address="1/1/1")
        rv_2 = RemoteValueRaw(xknx, payload_length=2, group_address="1/2/2")

        telegram = Telegram(
            destination_address=GroupAddress("1/0/0"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await rv_0.process(telegram)
        assert rv_0.value == 0

        telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueWrite(DPTArray((0x64,))),
        )
        await rv_1.process(telegram)
        assert rv_1.value == 100

        telegram = Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTArray((0x12, 0x34))),
        )
        await rv_2.process(telegram)
        assert rv_2.value == 4660

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        rv_0 = RemoteValueRaw(xknx, payload_length=0, group_address="1/0/0")
        rv_1 = RemoteValueRaw(xknx, payload_length=1, group_address="1/1/1")
        rv_2 = RemoteValueRaw(xknx, payload_length=2, group_address="1/2/2")

        telegram = Telegram(
            destination_address=GroupAddress("1/0/0"),
            payload=GroupValueWrite(DPTArray((0x01,))),
        )
        assert await rv_0.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/0/0"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await rv_0.process(telegram) is False
        assert rv_0.value is None

        telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await rv_1.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await rv_1.process(telegram) is False
        assert rv_1.value is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await rv_2.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/2"),
            payload=GroupValueWrite(DPTArray((0x64,))),
        )
        assert await rv_2.process(telegram) is False
        assert rv_2.value is None

    def test_to_knx_error(self):
        """Test to_knx function with wrong parameters."""
        xknx = XKNX()
        rv_0 = RemoteValueRaw(xknx, payload_length=0, group_address="1/0/0")
        rv_1 = RemoteValueRaw(xknx, payload_length=1, group_address="1/1/1")
        rv_2 = RemoteValueRaw(xknx, payload_length=2, group_address="1/2/2")

        with pytest.raises(ConversionError):
            rv_0.to_knx(-1)
        with pytest.raises(ConversionError):
            rv_0.to_knx(64)
        with pytest.raises(ConversionError):
            rv_0.to_knx(5.5)
        with pytest.raises(ConversionError):
            rv_0.to_knx("a")

        with pytest.raises(ConversionError):
            rv_1.to_knx(-1)
        with pytest.raises(ConversionError):
            rv_1.to_knx(256)
        with pytest.raises(ConversionError):
            rv_1.to_knx(5.5)
        with pytest.raises(ConversionError):
            rv_1.to_knx("a")

        with pytest.raises(ConversionError):
            rv_2.to_knx(-1)
        with pytest.raises(ConversionError):
            rv_2.to_knx(65536)
        with pytest.raises(ConversionError):
            rv_2.to_knx(5.5)
        with pytest.raises(ConversionError):
            rv_2.to_knx("a")
