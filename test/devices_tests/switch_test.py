"""Unit test for Switch objects."""
import asyncio
import unittest
from unittest.mock import MagicMock, Mock, patch

from xknx import XKNX
from xknx.devices import Switch
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramType


class AsyncMock(MagicMock):
    """Async Mock."""

    # pylint: disable=invalid-overridden-method
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


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
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address_state="1/2/3")
        self.loop.run_until_complete(switch.sync())

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), TelegramType.GROUP_READ)
        )

    def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Test with Switch with explicit state address."""
        xknx = XKNX()
        switch = Switch(
            xknx, "TestOutlet", group_address="1/2/3", group_address_state="1/2/4"
        )
        self.loop.run_until_complete(switch.sync())

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/4"), TelegramType.GROUP_READ)
        )

    #
    # TEST PROCESS
    #
    def test_process(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = AsyncMock()

        switch1 = Switch(
            xknx, "TestOutlet", group_address="1/2/3", device_updated_cb=callback_mock
        )
        switch2 = Switch(
            xknx, "TestOutlet", group_address="1/2/3", device_updated_cb=callback_mock
        )
        self.assertEqual(switch1.state, None)
        self.assertEqual(switch2.state, None)
        callback_mock.assert_not_called()

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )
        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(0)
        )

        self.loop.run_until_complete(switch1.process(telegram_on))
        self.assertEqual(switch1.state, True)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        self.loop.run_until_complete(switch1.process(telegram_off))
        self.assertEqual(switch1.state, False)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        # test setting switch2 to False with first telegram
        self.loop.run_until_complete(switch2.process(telegram_off))
        self.assertEqual(switch2.state, False)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        self.loop.run_until_complete(switch2.process(telegram_on))
        self.assertEqual(switch2.state, True)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    def test_process_state(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = AsyncMock()

        switch1 = Switch(
            xknx,
            "TestOutlet",
            group_address="1/2/3",
            group_address_state="1/2/4",
            device_updated_cb=callback_mock,
        )
        switch2 = Switch(
            xknx,
            "TestOutlet",
            group_address="1/2/3",
            group_address_state="1/2/4",
            device_updated_cb=callback_mock,
        )
        self.assertEqual(switch1.state, None)
        self.assertEqual(switch2.state, None)
        callback_mock.assert_not_called()

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=DPTBinary(1),
            telegramtype=TelegramType.GROUP_RESPONSE,
        )
        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=DPTBinary(0),
            telegramtype=TelegramType.GROUP_RESPONSE,
        )

        self.loop.run_until_complete(switch1.process(telegram_on))
        self.assertEqual(switch1.state, True)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        self.loop.run_until_complete(switch1.process(telegram_off))
        self.assertEqual(switch1.state, False)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        # test setting switch2 to False with first telegram
        self.loop.run_until_complete(switch2.process(telegram_off))
        self.assertEqual(switch2.state, False)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        self.loop.run_until_complete(switch2.process(telegram_on))
        self.assertEqual(switch2.state, True)
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    def test_process_invert(self):
        """Test process / reading telegrams from telegram queue with inverted switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3", invert=True)
        self.assertEqual(switch.state, None)

        telegram_inv_on = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(0)
        )
        telegram_inv_off = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )

        self.loop.run_until_complete(switch.process(telegram_inv_on))
        self.assertEqual(switch.state, True)
        self.loop.run_until_complete(switch.process(telegram_inv_off))
        self.assertEqual(switch.state, False)

    def test_process_reset_after(self):
        """Test process reset_after."""
        xknx = XKNX()
        reset_after_sec = 0.001
        switch = Switch(
            xknx, "TestInput", group_address="1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )

        self.loop.run_until_complete(switch.process(telegram_on))
        self.assertTrue(switch.state)
        self.assertEqual(xknx.telegrams.qsize(), 0)
        self.loop.run_until_complete(asyncio.sleep(reset_after_sec * 2))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        self.loop.run_until_complete(switch.process(xknx.telegrams.get_nowait()))
        self.assertFalse(switch.state)

    def test_process_reset_after_cancel_existing(self):
        """Test process reset_after cancels existing reset tasks."""
        xknx = XKNX()
        reset_after_sec = 0.01
        switch = Switch(
            xknx, "TestInput", group_address="1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )

        self.loop.run_until_complete(switch.process(telegram_on))
        self.assertTrue(switch.state)
        self.assertEqual(xknx.telegrams.qsize(), 0)
        self.loop.run_until_complete(asyncio.sleep(reset_after_sec / 2))
        # half way through the reset timer
        self.loop.run_until_complete(switch.process(telegram_on))
        self.assertTrue(switch.state)

        self.loop.run_until_complete(asyncio.sleep(reset_after_sec / 2))
        self.assertEqual(xknx.telegrams.qsize(), 0)

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        # pylint: disable=no-self-use

        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(1)
        )
        self.loop.run_until_complete(switch.process(telegram))

        after_update_callback.assert_called_with(switch)

    #
    # TEST SET ON
    #
    def test_set_on(self):
        """Test switching on switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        self.loop.run_until_complete(switch.set_on())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTBinary(1))
        )

    #
    # TEST SET OFF
    #
    def test_set_off(self):
        """Test switching off switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        self.loop.run_until_complete(switch.set_off())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTBinary(0))
        )

    #
    # TEST SET INVERT
    #
    def test_set_invert(self):
        """Test switching on/off inverted switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3", invert=True)

        self.loop.run_until_complete(switch.set_on())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTBinary(0))
        )

        self.loop.run_until_complete(switch.set_off())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/3"), payload=DPTBinary(1))
        )

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        self.loop.run_until_complete(switch.do("on"))
        self.loop.run_until_complete(xknx.devices.process(xknx.telegrams.get_nowait()))
        self.assertTrue(switch.state)
        self.loop.run_until_complete(switch.do("off"))
        self.loop.run_until_complete(xknx.devices.process(xknx.telegrams.get_nowait()))
        self.assertFalse(switch.state)

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(switch.do("execute"))
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "TestOutlet"
            )
        self.assertEqual(xknx.telegrams.qsize(), 0)

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        self.assertTrue(switch.has_group_address(GroupAddress("1/2/3")))
        self.assertFalse(switch.has_group_address(GroupAddress("2/2/2")))
