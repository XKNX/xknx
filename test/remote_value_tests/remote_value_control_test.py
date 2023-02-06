"""Unit test for RemoteValueControl objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueControl
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueControl:
    """Test class for RemoteValueControl objects."""

    def test_wrong_value_type(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with pytest.raises(ConversionError):
            RemoteValueControl(xknx, value_type="wrong_value_type")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueControl(
            xknx, group_address=GroupAddress("1/2/3"), value_type="stepwise"
        )
        await remote_value.set(25)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0xB)),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueControl(
            xknx, group_address=GroupAddress("1/2/3"), value_type="stepwise"
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0xB)),
        )
        assert remote_value.value is None
        await remote_value.process(telegram)
        assert remote_value.value == 25

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueControl(
            xknx, group_address=GroupAddress("1/2/3"), value_type="stepwise"
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0x01)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0x10)),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
