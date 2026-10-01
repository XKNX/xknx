"""Unit test for RemoteValueScalingSpeed objects."""

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, ScalingSpeed
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueScalingSpeed
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueScalingSpeed:
    """Test class for RemoteValueScalingSpeed objects."""

    def test_to_knx(self) -> None:
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueScalingSpeed(xknx)
        assert remote_value.to_knx(
            ScalingSpeed(time_period=6.0, percent=100)
        ) == DPTArray((0x00, 0x3C, 0xFF))
        assert remote_value.to_knx(
            ScalingSpeed(time_period=1.0, percent=50)
        ) == DPTArray((0x00, 0x0A, 0x80))

    def test_from_knx(self) -> None:
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueScalingSpeed(xknx)
        assert remote_value.from_knx(DPTArray((0x00, 0x3C, 0xFF))) == ScalingSpeed(
            time_period=6.0, percent=100
        )

    def test_to_knx_error(self) -> None:
        """Test to_knx function with wrong parameters."""
        xknx = XKNX()
        remote_value = RemoteValueScalingSpeed(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx(ScalingSpeed(time_period=0.0, percent=50))
        with pytest.raises(ConversionError):
            remote_value.to_knx(ScalingSpeed(time_period=6553.6, percent=50))
        with pytest.raises(ConversionError):
            remote_value.to_knx(ScalingSpeed(time_period=1.0, percent=101))
        with pytest.raises(ConversionError):
            remote_value.to_knx(ScalingSpeed(time_period=1.0, percent=-1))

    async def test_set(self) -> None:
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueScalingSpeed(
            xknx, group_address=GroupAddress("1/2/3")
        )
        remote_value.set(ScalingSpeed(time_period=6.0, percent=100))
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00, 0x3C, 0xFF))),
        )

    def test_process(self) -> None:
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueScalingSpeed(
            xknx, group_address=GroupAddress("1/2/3")
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x00, 0x0A, 0x80))),
        )
        remote_value.process(telegram)
        assert remote_value.value == ScalingSpeed(time_period=1.0, percent=50)

    def test_to_process_error(self) -> None:
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueScalingSpeed(
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
