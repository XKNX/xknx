"""Unit test for Switch objects."""
import asyncio
from unittest.mock import Mock, patch
import pytest

from xknx import XKNX
from xknx.devices import Switch
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramType

from xknx._test import Testcase

class TestSwitch(Testcase):
    """Test class for Switch object."""

    #
    # SYNC
    #
    @pytest.mark.asyncio
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address_state='1/2/3')
        await switch.sync(False)

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = await xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    @pytest.mark.asyncio
    async def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Test with Switch with explicit state address."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet",
                        group_address='1/2/3',
                        group_address_state='1/2/4')
        await switch.sync(False)

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = await xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    #
    # TEST PROCESS
    #
    @pytest.mark.asyncio
    async def test_process(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')

        self.assertEqual(switch.state, False)

        telegram_on = Telegram()
        telegram_on.group_address = GroupAddress('1/2/3')
        telegram_on.payload = DPTBinary(1)
        await switch.process(telegram_on)

        self.assertEqual(switch.state, True)

        telegram_off = Telegram()
        telegram_off.group_address = GroupAddress('1/2/3')
        telegram_off.payload = DPTBinary(0)
        await switch.process(telegram_off)

        self.assertEqual(switch.state, False)

    @pytest.mark.asyncio
    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        # pylint: disable=no-self-use

        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram()
        telegram.group_address = GroupAddress('1/2/3')
        telegram.payload = DPTBinary(1)
        await switch.process(telegram)

        after_update_callback.assert_called_with(switch)

    #
    # TEST SET ON
    #
    @pytest.mark.asyncio
    async def test_set_on(self):
        """Test switching on switch."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        await switch.set_on()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(1)))

    #
    # TEST SET OFF
    #
    @pytest.mark.asyncio
    async def test_set_off(self):
        """Test switching off switch."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        await switch.set_off()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTBinary(0)))

    #
    # TEST DO
    #
    @pytest.mark.asyncio
    async def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        await switch.do("on")
        self.assertTrue(switch.state)
        await switch.do("off")
        self.assertFalse(switch.state)

    @pytest.mark.asyncio
    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        with patch('logging.Logger.warning') as mock_warn:
            await switch.do("execute")
            mock_warn.assert_called_with('Could not understand action %s for device %s', 'execute', 'TestOutlet')
        self.assertEqual(xknx.telegrams.qsize(), 0)

    #
    # TEST has_group_address
    #
    @pytest.mark.asyncio
    async def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        switch = Switch(xknx, 'TestOutlet', group_address='1/2/3')
        self.assertTrue(switch.has_group_address(GroupAddress('1/2/3')))
        self.assertFalse(switch.has_group_address(GroupAddress('2/2/2')))
