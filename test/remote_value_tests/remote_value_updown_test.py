"""Unit test for RemoteValueUpDown objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueUpDown
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueUpDown:
    """Test class for RemoteValueUpDown objects."""

    def test_to_knx(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx)
        assert remote_value.to_knx(RemoteValueUpDown.Direction.UP) == DPTBinary(0)
        assert remote_value.to_knx(RemoteValueUpDown.Direction.DOWN) == DPTBinary(1)

    def test_from_knx(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx)
        assert remote_value.from_knx(DPTBinary(0)) == RemoteValueUpDown.Direction.UP
        assert remote_value.from_knx(DPTBinary(1)) == RemoteValueUpDown.Direction.DOWN

    def test_to_knx_invert(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, invert=True)
        assert remote_value.to_knx(RemoteValueUpDown.Direction.UP) == DPTBinary(1)
        assert remote_value.to_knx(RemoteValueUpDown.Direction.DOWN) == DPTBinary(0)

    def test_from_knx_invert(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, invert=True)
        assert remote_value.from_knx(DPTBinary(0)) == RemoteValueUpDown.Direction.DOWN
        assert remote_value.from_knx(DPTBinary(1)) == RemoteValueUpDown.Direction.UP

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(1)

    async def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, group_address=GroupAddress("1/2/3"))
        remote_value.down()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        remote_value.up()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert remote_value.value is None
        remote_value.process(telegram)
        assert remote_value.value == RemoteValueUpDown.Direction.DOWN

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0x01)),
        )
        assert remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(3)),
        )
        assert remote_value.process(telegram) is False

        assert remote_value.value is None
