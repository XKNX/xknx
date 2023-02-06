"""Unit test for RemoteValueStep objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueStep
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueStep:
    """Test class for RemoteValueStep objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx)
        assert remote_value.to_knx(RemoteValueStep.Direction.INCREASE) == DPTBinary(1)
        assert remote_value.to_knx(RemoteValueStep.Direction.DECREASE) == DPTBinary(0)

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx)
        assert remote_value.from_knx(DPTBinary(1)) == RemoteValueStep.Direction.INCREASE
        assert remote_value.from_knx(DPTBinary(0)) == RemoteValueStep.Direction.DECREASE

    def test_to_knx_invert(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, invert=True)
        assert remote_value.to_knx(RemoteValueStep.Direction.INCREASE) == DPTBinary(0)
        assert remote_value.to_knx(RemoteValueStep.Direction.DECREASE) == DPTBinary(1)

    def test_from_knx_invert(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, invert=True)
        assert remote_value.from_knx(DPTBinary(1)) == RemoteValueStep.Direction.DECREASE
        assert remote_value.from_knx(DPTBinary(0)) == RemoteValueStep.Direction.INCREASE

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(1)

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.decrease()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await remote_value.increase()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        assert remote_value.value is None
        await remote_value.process(telegram)
        assert remote_value.value == RemoteValueStep.Direction.DECREASE

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0x01)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(3)),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
