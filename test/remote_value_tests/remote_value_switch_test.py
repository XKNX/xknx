"""Unit test for RemoteValueSwitch objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueSwitch
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueSwitch:
    """Test class for RemoteValueSwitch objects."""

    def test_to_knx(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        assert remote_value.to_knx(True) == DPTBinary(True)
        assert remote_value.to_knx(False) == DPTBinary(False)

    def test_from_knx(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        assert remote_value.from_knx(DPTBinary(True)) is True
        assert remote_value.from_knx(DPTBinary(0)) is False

    def test_to_knx_invert(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, invert=True)
        assert remote_value.to_knx(True) == DPTBinary(0)
        assert remote_value.to_knx(False) == DPTBinary(1)

    def test_from_knx_invert(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, invert=True)
        assert remote_value.from_knx(DPTBinary(1)) is False
        assert remote_value.from_knx(DPTBinary(0)) is True

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(1)

    async def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address=GroupAddress("1/2/3"))
        remote_value.on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        remote_value.off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert remote_value.value is None
        remote_value.process(telegram)
        assert remote_value.telegram is not None
        assert remote_value.value is True

    def test_process_off(self) -> None:
        """Test process OFF telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        assert remote_value.value is None
        remote_value.process(telegram)
        assert remote_value.telegram is not None
        assert remote_value.value is False

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, group_address=GroupAddress("1/2/3"))

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
