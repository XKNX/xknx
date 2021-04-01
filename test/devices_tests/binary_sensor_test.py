"""Unit test for BinarySensor objects."""
import asyncio
from unittest.mock import patch

import pytest
from xknx import XKNX
from xknx.devices import Action, BinarySensor, Switch
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

from test.util import AsyncMock


# pylint: disable=no-self-use
@pytest.mark.asyncio
class TestBinarySensor:
    """Test class for BinarySensor objects."""

    #
    # TEST PROCESS
    #
    async def test_process(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")

        assert binaryinput.state is None

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await binaryinput.process(telegram_on)
        assert binaryinput.state is True

        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await binaryinput.process(telegram_off)
        assert binaryinput.state is False

        binaryinput2 = BinarySensor(xknx, "TestInput", "1/2/4")
        assert binaryinput2.state is None

        telegram_off2 = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await binaryinput2.process(telegram_off2)
        assert binaryinput2.state is False

    async def test_process_invert(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        bs_invert = BinarySensor(xknx, "TestInput", "1/2/3", invert=True)

        assert bs_invert.state is None

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await bs_invert.process(telegram_on)

        assert bs_invert.state is True

        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await bs_invert.process(telegram_off)
        assert bs_invert.state is False

    async def test_process_reset_after(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        reset_after_sec = 0.001
        async_after_update_callback = AsyncMock()
        binaryinput = BinarySensor(
            xknx,
            "TestInput",
            "1/2/3",
            reset_after=reset_after_sec,
            device_updated_cb=async_after_update_callback,
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await binaryinput.process(telegram_on)
        assert binaryinput.state
        await asyncio.sleep(reset_after_sec * 1.2)
        assert not binaryinput.state
        # once for 'on' and once for 'off'
        assert async_after_update_callback.call_count == 2

        async_after_update_callback.reset_mock()
        # multiple telegrams during reset_after time period shall reset timer
        await binaryinput.process(telegram_on)
        async_after_update_callback.assert_called_once()
        await binaryinput.process(telegram_on)
        await binaryinput.process(telegram_on)
        # second and third telegram resets timer but doesn't run callback
        async_after_update_callback.assert_called_once()
        assert binaryinput.state
        await asyncio.sleep(reset_after_sec * 1.2)
        assert not binaryinput.state
        # once for 'on' and once for 'off'
        assert async_after_update_callback.call_count == 2

    async def test_process_action(self):
        """Test process / reading telegrams from telegram queue. Test if action is executed."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")

        binary_sensor = BinarySensor(xknx, "TestInput", group_address_state="1/2/3")
        action_on = Action(xknx, hook="on", target="TestOutlet", method="on")
        binary_sensor.actions.append(action_on)
        action_off = Action(xknx, hook="off", target="TestOutlet", method="off")
        binary_sensor.actions.append(action_off)

        assert binary_sensor.state is None
        assert switch.state is None

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await binary_sensor.process(telegram_on)
        # process outgoing telegram from queue
        await switch.process(xknx.telegrams.get_nowait())

        assert binary_sensor.state is True
        assert switch.state is True

        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        await binary_sensor.process(telegram_off)
        await switch.process(xknx.telegrams.get_nowait())

        assert binary_sensor.state is False
        assert switch.state is False

    async def test_process_action_ignore_internal_state(self):
        """Test process / reading telegrams from telegram queue. Test if action is executed."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="5/5/5")

        binary_sensor = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", ignore_internal_state=True
        )
        action_on = Action(xknx, hook="on", target="TestOutlet", method="on")
        binary_sensor.actions.append(action_on)

        assert binary_sensor.state is None
        assert switch.state is None

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        with patch("time.time") as mock_time, patch(
            "asyncio.sleep", new_callable=AsyncMock
        ):
            mock_time.return_value = 1599076123.0
            await binary_sensor.process(telegram_on)
            await xknx.devices.process(xknx.telegrams.get_nowait())

            assert binary_sensor.state is True
            assert switch.state is True

            await switch.set_off()
            await xknx.devices.process(xknx.telegrams.get_nowait())

            assert switch.state is False
            assert binary_sensor.state is True

            await binary_sensor.process(telegram_on)
            await xknx.devices.process(xknx.telegrams.get_nowait())

            assert binary_sensor.state is True
            assert switch.state is True

    async def test_process_wrong_payload(self):
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        binary_sensor = BinarySensor(xknx, "Warning", group_address_state="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x1, 0x2, 0x3))),
        )
        with pytest.raises(CouldNotParseTelegram):
            await binary_sensor.process(telegram)

    #
    # TEST SWITCHED ON
    #
    async def test_is_on(self):
        """Test is_on() and is_off() of a BinarySensor with state 'on'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")
        assert not binaryinput.is_on()
        assert binaryinput.is_off()
        # pylint: disable=protected-access
        await binaryinput._set_internal_state(True)

        assert binaryinput.is_on()
        assert not binaryinput.is_off()

    #
    # TEST SWITCHED OFF
    #
    async def test_is_off(self):
        """Test is_on() and is_off() of a BinarySensor with state 'off'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")
        # pylint: disable=protected-access
        await binaryinput._set_internal_state(False)

        assert not binaryinput.is_on()
        assert binaryinput.is_off()

    #
    # TEST PROCESS CALLBACK
    #
    async def test_process_callback(self):
        """Test after_update_callback after state of switch was changed."""
        # pylint: disable=protected-access
        xknx = XKNX()
        switch = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", ignore_internal_state=False
        )
        async_after_update_callback = AsyncMock()

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await switch.process(telegram)
        # no _context_task started because ignore_internal_state is False
        assert switch._context_task is None
        async_after_update_callback.assert_called_once_with(switch)

        async_after_update_callback.reset_mock()
        # send same telegram again
        await switch.process(telegram)
        async_after_update_callback.assert_not_called()

    async def test_process_callback_ignore_internal_state(self):
        """Test after_update_callback after state of switch was changed."""
        # pylint: disable=protected-access
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            ignore_internal_state=True,
            context_timeout=0.001,
        )
        async_after_update_callback = AsyncMock()

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert switch.counter == 0

        await switch.process(telegram)
        async_after_update_callback.assert_not_called()
        assert switch.counter == 1
        await switch._context_task
        async_after_update_callback.assert_called_with(switch)
        # once with counter 1 and once with counter 0
        assert async_after_update_callback.call_count == 2

        async_after_update_callback.reset_mock()
        # send same telegram again
        await switch.process(telegram)
        assert switch.counter == 1
        await switch.process(telegram)
        assert switch.counter == 2
        async_after_update_callback.assert_not_called()

        await switch._context_task
        async_after_update_callback.assert_called_with(switch)
        # once with counter 2 and once with counter 0
        assert async_after_update_callback.call_count == 2
        assert switch.counter == 0

    async def test_process_callback_ignore_internal_state_no_counter(self):
        """Test after_update_callback after state of switch was changed."""
        # pylint: disable=protected-access
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            ignore_internal_state=True,
            context_timeout=0,
        )
        async_after_update_callback = AsyncMock()

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await switch.process(telegram)
        # no _context_task started because context_timeout is False
        assert switch._context_task is None
        async_after_update_callback.assert_called_once_with(switch)

        async_after_update_callback.reset_mock()
        # send same telegram again
        await switch.process(telegram)
        async_after_update_callback.assert_called_once_with(switch)

    async def test_process_group_value_response(self):
        """Test precess of GroupValueResponse telegrams."""
        # pylint: disable=protected-access
        xknx = XKNX()
        switch = BinarySensor(
            xknx,
            "TestInput",
            group_address_state="1/2/3",
            ignore_internal_state=True,
        )
        async_after_update_callback = AsyncMock()

        switch.register_device_updated_cb(async_after_update_callback)

        write_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        response_telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(
                DPTBinary(1),
            ),
        )
        assert switch.state is None
        # initial GroupValueResponse changes state and runs callback
        await switch.process(response_telegram)
        assert switch.state
        async_after_update_callback.assert_called_once_with(switch)
        # GroupValueWrite with same payload runs callback because of `ignore_internal_state`
        async_after_update_callback.reset_mock()
        await switch.process(write_telegram)
        assert switch.state
        async_after_update_callback.assert_called_once_with(switch)
        # GroupValueResponse should not run callback when state has not changed
        async_after_update_callback.reset_mock()
        await switch.process(response_telegram)
        async_after_update_callback.assert_not_called()

    #
    # TEST COUNTER
    #
    def test_counter(self):
        """Test counter functionality."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", context_timeout=1
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = 1517000000.0
            assert switch.bump_and_get_counter(True) == 1

            mock_time.return_value = 1517000000.1
            assert switch.bump_and_get_counter(True) == 2

            mock_time.return_value = 1517000000.2
            assert switch.bump_and_get_counter(False) == 1

            mock_time.return_value = 1517000000.3
            assert switch.bump_and_get_counter(True) == 3

            mock_time.return_value = 1517000000.4
            assert switch.bump_and_get_counter(False) == 2

            mock_time.return_value = 1517000002.0  # TIME OUT ...
            assert switch.bump_and_get_counter(True) == 1

            mock_time.return_value = 1517000004.1  # TIME OUT ...
            assert switch.bump_and_get_counter(False) == 1

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        switch = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", context_timeout=1
        )
        assert switch.unique_id == "1/2/3"
