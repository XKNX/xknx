"""Unit test for RemoteValueSceneNumber objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueTemp
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueTemp:
    """Test class for RemoteValueTemp objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueTemp(xknx)
        assert remote_value.to_knx(11) == DPTArray((0x04, 0x4C))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueTemp(xknx)
        assert remote_value.from_knx(DPTArray((0x04, 0x4C))) == 11

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueTemp(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(-300)
        with pytest.raises(ConversionError):
            remote_value.to_knx("abc")

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueTemp(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x04, 0x4C))),
        )
        await remote_value.process(telegram)
        assert remote_value.value == 11

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueTemp(xknx, group_address=GroupAddress("1/2/3"))

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

        assert remote_value.value is None
