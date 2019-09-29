"""Unit test for Switch objects."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import Switch
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestSwitch(unittest.TestCase):
    """Test class for Switch object."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, "TestOutlet", group_address_state='1/2/3')
        self.loop.run_until_complete(asyncio.Task(switch.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Test with Switch with explicit state address."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, "TestOutlet",
                        group_address='1/2/3',
                        group_address_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(switch.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    def test_process(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')

        self.assertEqual(switch.state, False)

        telegram_on = Telegram()
        telegram_on.group_address = GroupAddress('1/2/3')
        telegram_on.payload = DPTBinary(1)
        self.loop.run_until_complete(asyncio.Task(switch.process(telegram_on)))

        self.assertEqual(switch.state, True)

        telegram_off = Telegram()
        telegram_off.group_address = GroupAddress('1/2/3')
        telegram_off.payload = DPTBinary(0)
        self.loop.run_until_complete(asyncio.Task(switch.process(telegram_off)))

        self.assertEqual(switch.state, False)

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        # pylint: disable=no-self-use

        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram()
        telegram.group_address = GroupAddress('1/2/3')
        telegram.payload = DPTBinary(1)
        self.loop.run_until_complete(asyncio.Task(switch.process(telegram)))

        after_update_callback.assert_called_with(switch)

    #
    # TEST SET ON
    #
    def test_set_on(self):
        """Test switching on switch."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        self.loop.run_until_complete(asyncio.Task(switch.set_on()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1)))

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        """Test switching off switch."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        self.loop.run_until_complete(asyncio.Task(switch.set_off()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(0)))

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        self.loop.run_until_complete(asyncio.Task(switch.do("on")))
        self.assertTrue(switch.state)
        self.loop.run_until_complete(asyncio.Task(switch.do("off")))
        self.assertFalse(switch.state)

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            self.loop.run_until_complete(asyncio.Task(switch.do("execute")))
            mock_warn.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestOutlet')
        self.assertEqual(xknx.telegrams.qsize(), 0)

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX(loop=self.loop)
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        self.assertTrue(switch.has_group_address(GroupAddress('1/2/3')))
        self.assertFalse(switch.has_group_address(GroupAddress('2/2/2')))
