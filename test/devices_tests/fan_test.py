"""Unit test for Fan objects."""
from unittest.mock import AsyncMock, patch

from xknx import XKNX
from xknx.devices import Fan
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


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
    # TEST SWITCH ON/OFF
    #
    async def test_switch_on_off(self):
        """Test switching on/off of a Fan."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")

        # Turn the fan on via speed GA. First try without providing a speed,
        # which will set it to the default 50% percentage.
        await fan.turn_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # 128 is 50% as byte (0...255)
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(128)),
        )

        # Try again, but this time with a speed provided
        await fan.turn_on(55)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # 140 is 55% as byte (0...255)
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )

        # Turn the fan off via the speed GA
        await fan.turn_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0)),
        )

        fan_with_switch = Fan(
            xknx,
            name="TestFanSwitch",
            group_address_speed="1/2/3",
            group_address_switch="4/5/6",
        )

        # Turn the fan on via the switch GA, which should not adjust the speed
        await fan_with_switch.turn_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("4/5/6"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        # Turn the fan off via the switch GA
        await fan_with_switch.turn_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("4/5/6"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        # Turn the fan on again this time with a provided speed, which for a switch GA fan
        # should result in separate telegrams to switch on the fan and then set the speed.
        await fan_with_switch.turn_on(55)
        assert xknx.telegrams.qsize() == 2
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("4/5/6"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )

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
        await fan.process(telegram)
        assert fan.is_on is True

        # A speed of 0 will turn off the fan implicitly if there is no
        # dedicated switch GA
        await fan.set_speed(0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        # 140 is 55% as byte (0...255)
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0)),
        )
        await fan.process(telegram)
        assert fan.is_on is False

        fan_with_switch = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            group_address_switch="4/5/6",
        )
        await fan_with_switch.turn_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("4/5/6"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await fan_with_switch.process(telegram)
        assert fan_with_switch.is_on is True

        # A speed of 0 will not turn off the fan implicitly if there is a
        # dedicated switch GA defined. So we only expect a speed change telegram,
        # but no state switch one.
        await fan_with_switch.set_speed(0)
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0)),
        )
        await fan_with_switch.process(telegram)
        assert fan_with_switch.is_on is True

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
    # TEST PROCESS SPEED
    #
    async def test_process_speed(self):
        """Test process / reading telegrams from telegram queue. Test if speed is processed."""
        xknx = XKNX()
        fan = Fan(xknx, name="TestFan", group_address_speed="1/2/3")
        assert fan.is_on is False
        assert fan.current_speed is None

        # 140 is 55% as byte (0...255)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )
        await fan.process(telegram)
        # Setting a speed for a fan that has no dedicated switch GA,
        # should turn on the fan.
        assert fan.is_on is True
        assert fan.current_speed == 55

        # Now set a speed of zero which should turn off the fan.
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0)),
        )
        await fan.process(telegram)
        assert fan.is_on is False
        assert fan.current_speed == 0

    async def test_process_speed_wrong_payload(self):
        """Test process wrong telegrams. (wrong payload type)."""
        xknx = XKNX()
        cb_mock = AsyncMock()
        fan = Fan(
            xknx, name="TestFan", group_address_speed="1/2/3", device_updated_cb=cb_mock
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with patch("logging.Logger.warning") as log_mock:
            await fan.process(telegram)
            log_mock.assert_called_once()
            cb_mock.assert_not_called()

    #
    # TEST PROCESS SWITCH
    #
    async def test_process_switch(self):
        """Test process / reading telegrams from telegram queue. Test if switch is handled correctly."""
        xknx = XKNX()
        fan = Fan(
            xknx,
            name="TestFan",
            group_address_speed="1/2/3",
            group_address_switch="4/5/6",
        )
        assert fan.is_on is False
        assert fan.current_speed is None

        # 140 is 55% as byte (0...255)
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )
        await fan.process(telegram)
        # Setting a speed for a fan with dedicated switch GA,
        # should not turn on the fan
        assert fan.is_on is False
        assert fan.current_speed == 55

        # Now turn on the fan via its switch GA
        telegram = Telegram(
            destination_address=GroupAddress("4/5/6"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await fan.process(telegram)
        assert fan.is_on is True
        assert fan.current_speed == 55

        # Setting a speed of 0 should not turn off the fan
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(0)),
        )
        await fan.process(telegram)
        assert fan.is_on is True
        assert fan.current_speed == 0

        # Set the speed again so we can verify that switching off the fan does not
        # modify the set speed
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(140)),
        )
        await fan.process(telegram)
        assert fan.is_on is True
        assert fan.current_speed == 55

        # Now turn off the fan via the dedicated switch GA
        telegram = Telegram(
            destination_address=GroupAddress("4/5/6"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await fan.process(telegram)
        assert fan.is_on is False
        assert fan.current_speed == 55

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
        cb_mock = AsyncMock()
        fan = Fan(
            xknx, name="TestFan", group_address_speed="1/2/3", device_updated_cb=cb_mock
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with patch("logging.Logger.warning") as log_mock:
            await fan.process(telegram)
            log_mock.assert_called_once()
            cb_mock.assert_not_called()

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
            group_address_switch="1/5/1",
            group_address_switch_state="1/5/2",
        )
        assert fan.has_group_address(GroupAddress("1/7/1"))
        assert fan.has_group_address(GroupAddress("1/7/2"))
        assert not fan.has_group_address(GroupAddress("1/7/3"))
        assert fan.has_group_address(GroupAddress("1/6/1"))
        assert fan.has_group_address(GroupAddress("1/6/2"))
        assert fan.has_group_address(GroupAddress("1/5/1"))
        assert fan.has_group_address(GroupAddress("1/5/2"))
