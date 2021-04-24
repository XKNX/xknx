"""Unit test for Fan objects."""
import pytest
from xknx import XKNX
from xknx.devices import Fan
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


@pytest.mark.asyncio
class TestFan:
    """Class for testing Fan objects."""

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed_state="1/2/3")
        await fan.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    async def test_sync_step(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed_state="1/2/3",
        )
        await fan.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    #
    # SYNC WITH STATE ADDRESS
    #
    async def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            group_address_speed_state="1/2/4",
        )
        await fan.sync()
        assert xknx.telegrams.qsize() == 1
        telegram1 = xknx.telegrams.get_nowait()
        assert telegram1 == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    #
    #
    # TEST SET SPEED
    #
    async def test_set_speed(self):
        """Test setting the speed of a Fan."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        await fan.set_speed(55)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # 140 is 55% as byte (0...255)
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )

    #
    #
    # TEST SET SPEED STEP
    #
    async def test_set_speed_step(self):
        """Test setting the speed of a Fan in step mode."""

        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            max_step=3,
        )
        await fan.set_speed(2)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(2)),
        )

    #
    #
    # TEST SET OSCILLATION
    #
    async def test_set_oscillation(self):
        """Test setting the oscillation of a Fan."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            group_address_oscillation="1/2/5",
        )
        await fan.set_oscillation(False)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST PROCESS
    #
    async def test_process_speed(self):
        """Test process / reading telegrams from telegram queue. Test if speed is processed."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        assert fan.current_speed is None

        # 140 is 55% as byte (0...255)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )
        await fan.process(telegram)
        assert fan.current_speed == 55

    async def test_process_speed_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with pytest.raises(CouldNotParseTelegram):
            await fan.process(telegram)

    #
    # TEST PROCESS OSCILLATION
    #
    async def test_process_oscillation(self):
        """Test process / reading telegrams from telegram queue. Test if oscillation is processed."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            group_address_oscillation="1/2/5",
        )
        assert fan.current_oscillation is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/5"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await fan.process(telegram)
        assert fan.current_oscillation

    async def test_process_fan_payload_invalid_length(self):
        """Test process wrong telegrams. (wrong payload length)."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with pytest.raises(CouldNotParseTelegram):
            await fan.process(telegram)

    #
    # TEST PROCESS STEP MODE
    #
    async def test_process_speed_step(self):
        """Test process / reading telegrams from telegram queue. Test if speed is processed."""

        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            max_step=3,
        )
        assert fan.current_speed is None

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(2)),
        )
        await fan.process(telegram)
        assert fan.current_speed == 2

    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            "TestFan",
            group_address_speed="1/7/1",
            group_address_speed_state="1/7/2",
            group_address_oscillation="1/6/1",
            group_address_oscillation_state="1/6/2",
        )
        assert fan.has_group_address(GroupAddress("1/7/1"))
        assert fan.has_group_address(GroupAddress("1/7/2"))
        assert not fan.has_group_address(GroupAddress("1/7/3"))
        assert fan.has_group_address(GroupAddress("1/6/1"))
        assert fan.has_group_address(GroupAddress("1/6/2"))
