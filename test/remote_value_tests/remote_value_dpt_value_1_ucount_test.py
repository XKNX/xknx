"""Unit test for RemoteValueDptValue1Ucount objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueDptValue1Ucount
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueDptValue1Ucount:
    """Test class for RemoteValueDptValue1Ucount objects."""

    def test_to_knx(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(xknx)
        assert remote_value.to_knx(10) == DPTArray((0x0A,))

    def test_from_knx(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(xknx)
        assert remote_value.from_knx(DPTArray((0x0A,))) == 10

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(256)
        with pytest.raises(ConversionError):
            remote_value.to_knx("256")

    async def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(
            xknx, group_address=GroupAddress("1/2/3")
        )
        remote_value.set(10)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A,))),
        )
        remote_value.set(11)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0B,))),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(
            xknx, group_address=GroupAddress("1/2/3")
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x0A,))),
        )
        remote_value.process(telegram)
        assert remote_value.value == 10

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(
            xknx, group_address=GroupAddress("1/2/3")
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert remote_value.process(telegram) is False

        assert remote_value.value is None
