"""Unit test for RemoteValueColorXYY objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueColorXYY
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueColorXYY:
    """Test class for RemoteValueColorXYY objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorXYY(xknx)
        assert remote_value.to_knx(((1, 0.9), 102)) == DPTArray(
            (0xFF, 0xFF, 0xE6, 0x66, 0x66, 0x03)
        )
        assert remote_value.to_knx(((1, 0), 102)) == DPTArray(
            (0xFF, 0xFF, 0x00, 0x00, 0x66, 0x03)
        )

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorXYY(xknx)
        assert remote_value.from_knx(
            DPTArray((0x99, 0x99, 0x99, 0x99, 0x66, 0x03))
        ) == ((0.6, 0.6), 102)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueColorXYY(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(((2, 1), 1))
        with pytest.raises(ConversionError):
            remote_value.to_knx(((-1, 1), 2))
        with pytest.raises(ConversionError):
            remote_value.to_knx(((0.3, 0.5), 256))
        with pytest.raises(ConversionError):
            remote_value.to_knx((("0.4", 0), 102))
        with pytest.raises(ConversionError):
            remote_value.to_knx(((1, 1), "102"))
        with pytest.raises(ConversionError):
            remote_value.to_knx(((1,), 1))

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueColorXYY(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.set(((1, 0.9), 102))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0xFF, 0xFF, 0xE6, 0x66, 0x66, 0x03))),
        )
        await remote_value.set(((1, 0.9), 255))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0xFF, 0xFF, 0xE6, 0x66, 0xFF, 0x03))),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorXYY(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0xFF, 0xFF, 0x66, 0x66, 0xFA, 0x03))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == ((1, 0.4), 250)

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorXYY(xknx, group_address=GroupAddress("1/2/3"))

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
