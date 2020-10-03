"""Unit test for BinarySensor objects."""
import asyncio
import unittest
from unittest.mock import MagicMock, Mock, patch

from xknx import XKNX
from xknx.devices import Action, BinarySensor, Switch
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram


class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class TestBinarySensor(unittest.TestCase):
    """Test class for BinarySensor objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # TEST PROCESS
    #
    def test_process(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")

        self.assertEqual(binaryinput.state, None)

        telegram_on = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )
        self.loop.run_until_complete(binaryinput.process(telegram_on))

        self.assertEqual(binaryinput.state, True)

        telegram_off = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(0)
        )
        self.loop.run_until_complete(binaryinput.process(telegram_off))
        self.assertEqual(binaryinput.state, False)

        binaryinput2 = BinarySensor(xknx, "TestInput", "1/2/4")
        self.assertEqual(binaryinput2.state, None)

        telegram_off2 = Telegram(
            group_address=GroupAddress("1/2/4"), payload=DPTBinary(0)
        )
        self.loop.run_until_complete(binaryinput2.process(telegram_off2))
        self.assertEqual(binaryinput2.state, False)

    def test_process_reset_after(self):
        """Test process / reading telegrams from telegram queue."""
        xknx = XKNX()
        reset_after_sec = 0.001
        binaryinput = BinarySensor(
            xknx, "TestInput", "1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )

        self.loop.run_until_complete(binaryinput.process(telegram_on))
        self.loop.run_until_complete(asyncio.sleep(reset_after_sec * 2))
        self.assertEqual(binaryinput.state, False)

    def test_process_action(self):
        """Test process / reading telegrams from telegram queue. Test if action is executed."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")

        binary_sensor = BinarySensor(xknx, "TestInput", group_address_state="1/2/3")
        action_on = Action(xknx, hook="on", target="TestOutlet", method="on")
        binary_sensor.actions.append(action_on)
        action_off = Action(xknx, hook="off", target="TestOutlet", method="off")
        binary_sensor.actions.append(action_off)

        self.assertEqual(binary_sensor.state, None)
        self.assertEqual(switch.state, False)

        telegram_on = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )
        self.loop.run_until_complete(binary_sensor.process(telegram_on))
        # process outgoing telegram from queue
        self.loop.run_until_complete(switch.process(xknx.telegrams.get_nowait()))

        self.assertEqual(binary_sensor.state, True)
        self.assertEqual(switch.state, True)

        telegram_off = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(0)
        )
        self.loop.run_until_complete(binary_sensor.process(telegram_off))
        self.loop.run_until_complete(switch.process(xknx.telegrams.get_nowait()))

        self.assertEqual(binary_sensor.state, False)
        self.assertEqual(switch.state, False)

    def test_process_action_ignore_internal_state(self):
        """Test process / reading telegrams from telegram queue. Test if action is executed."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="5/5/5")

        binary_sensor = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", ignore_internal_state=True
        )
        action_on = Action(xknx, hook="on", target="TestOutlet", method="on")
        binary_sensor.actions.append(action_on)

        self.assertEqual(binary_sensor.state, None)
        self.assertEqual(switch.state, False)

        telegram_on = Telegram(
            group_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )

        with patch("time.time") as mock_time, patch(
            "asyncio.sleep", new_callable=AsyncMock
        ) as mock_sleep:
            mock_time.return_value = 1599076123.0
            self.loop.run_until_complete(binary_sensor.process(telegram_on))
            self.loop.run_until_complete(
                xknx.devices.process(xknx.telegrams.get_nowait())
            )
            self.assertEqual(binary_sensor.state, True)
            self.assertEqual(switch.state, True)

            self.loop.run_until_complete(switch.set_off())
            self.loop.run_until_complete(
                xknx.devices.process(xknx.telegrams.get_nowait())
            )
            self.assertEqual(switch.state, False)
            self.assertEqual(binary_sensor.state, True)

            self.loop.run_until_complete(binary_sensor.process(telegram_on))
            self.loop.run_until_complete(
                xknx.devices.process(xknx.telegrams.get_nowait())
            )
            self.assertEqual(binary_sensor.state, True)
            self.assertEqual(switch.state, True)

    def test_process_wrong_payload(self):
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        binary_sensor = BinarySensor(xknx, "Warning", group_address_state="1/2/3")
        telegram = Telegram(GroupAddress("1/2/3"), payload=DPTArray((0x1, 0x2, 0x3)))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(binary_sensor.process(telegram))

    #
    # TEST SWITCHED ON
    #
    def test_is_on(self):
        """Test is_on() and is_off() of a BinarySensor with state 'on'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")
        self.assertFalse(binaryinput.is_on())
        self.assertTrue(binaryinput.is_off())
        # pylint: disable=protected-access
        self.loop.run_until_complete(binaryinput._set_internal_state(True))

        self.assertTrue(binaryinput.is_on())
        self.assertFalse(binaryinput.is_off())

    #
    # TEST SWITCHED OFF
    #
    def test_is_off(self):
        """Test is_on() and is_off() of a BinarySensor with state 'off'."""
        xknx = XKNX()
        binaryinput = BinarySensor(xknx, "TestInput", "1/2/3")
        # pylint: disable=protected-access
        self.loop.run_until_complete(binaryinput._set_internal_state(False))

        self.assertFalse(binaryinput.is_on())
        self.assertTrue(binaryinput.is_off())

    #
    # TEST PROCESS CALLBACK
    #
    def test_process_callback(self):
        """Test after_update_callback after state of switch was changed."""
        # pylint: disable=protected-access
        xknx = XKNX()
        switch = BinarySensor(
            xknx, "TestInput", group_address_state="1/2/3", ignore_internal_state=False
        )

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(group_address=GroupAddress("1/2/3"), payload=DPTBinary(1))
        self.loop.run_until_complete(switch.process(telegram))
        # no _context_task started because ignore_internal_state is False
        self.assertIsNone(switch._context_task)
        after_update_callback.assert_called_once_with(switch)

        after_update_callback.reset_mock()
        # send same telegram again
        self.loop.run_until_complete(switch.process(telegram))
        after_update_callback.assert_not_called()

    def test_process_callback_ignore_internal_state(self):
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

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(group_address=GroupAddress("1/2/3"), payload=DPTBinary(1))
        self.assertEqual(switch.counter, 0)

        self.loop.run_until_complete(switch.process(telegram))
        after_update_callback.assert_not_called()
        self.assertEqual(switch.counter, 1)
        self.loop.run_until_complete(switch._context_task)
        after_update_callback.assert_called_with(switch)
        # once with counter 1 and once with counter 0
        self.assertEqual(after_update_callback.call_count, 2)

        after_update_callback.reset_mock()
        # send same telegram again
        self.loop.run_until_complete(switch.process(telegram))
        self.assertEqual(switch.counter, 1)
        self.loop.run_until_complete(switch.process(telegram))
        self.assertEqual(switch.counter, 2)
        after_update_callback.assert_not_called()

        self.loop.run_until_complete(switch._context_task)
        after_update_callback.assert_called_with(switch)
        # once with counter 2 and once with counter 0
        self.assertEqual(after_update_callback.call_count, 2)
        self.assertEqual(switch.counter, 0)

    def test_process_callback_ignore_internal_state_no_counter(self):
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

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(group_address=GroupAddress("1/2/3"), payload=DPTBinary(1))
        self.loop.run_until_complete(switch.process(telegram))
        # no _context_task started because context_timeout is False
        self.assertIsNone(switch._context_task)
        after_update_callback.assert_called_once_with(switch)

        after_update_callback.reset_mock()
        # send same telegram again
        self.loop.run_until_complete(switch.process(telegram))
        after_update_callback.assert_called_once_with(switch)

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
            self.assertEqual(switch.bump_and_get_counter(True), 1)

            mock_time.return_value = 1517000000.1
            self.assertEqual(switch.bump_and_get_counter(True), 2)

            mock_time.return_value = 1517000000.2
            self.assertEqual(switch.bump_and_get_counter(False), 1)

            mock_time.return_value = 1517000000.3
            self.assertEqual(switch.bump_and_get_counter(True), 3)

            mock_time.return_value = 1517000000.4
            self.assertEqual(switch.bump_and_get_counter(False), 2)

            mock_time.return_value = 1517000002.0  # TIME OUT ...
            self.assertEqual(switch.bump_and_get_counter(True), 1)

            mock_time.return_value = 1517000004.1  # TIME OUT ...
            self.assertEqual(switch.bump_and_get_counter(False), 1)
