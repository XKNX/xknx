"""Unit test for Notification objects."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import Notification
from xknx.dpt import DPTArray, DPTBinary, DPTString
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestNotification(unittest.TestCase):
    """Test class for Notification object."""

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
    def test_sync_state(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        notification = Notification(
            xknx, "Warning", group_address="1/2/3", group_address_state="1/2/4"
        )
        self.loop.run_until_complete(notification.sync())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram, Telegram(GroupAddress("1/2/4"), TelegramType.GROUP_READ)
        )

    #
    # TEST PROCESS
    #
    def test_process(self):
        """Test process telegram with notification. Test if device was updated."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        telegram_set = Telegram(
            GroupAddress("1/2/3"), payload=DPTArray(DPTString().to_knx("Ein Prosit!"))
        )
        self.loop.run_until_complete(notification.process(telegram_set))
        self.assertEqual(notification.message, "Ein Prosit!")

        telegram_unset = Telegram(
            GroupAddress("1/2/3"), payload=DPTArray(DPTString().to_knx(""))
        )
        self.loop.run_until_complete(notification.process(telegram_unset))
        self.assertEqual(notification.message, "")

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        # pylint: disable=no-self-use
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        notification.register_device_updated_cb(async_after_update_callback)
        telegram_set = Telegram(
            GroupAddress("1/2/3"), payload=DPTArray(DPTString().to_knx("Ein Prosit!"))
        )
        self.loop.run_until_complete(notification.process(telegram_set))
        after_update_callback.assert_called_with(notification)

    def test_process_payload_invalid_length(self):
        """Test process wrong telegram (wrong payload length)."""
        # pylint: disable=invalid-name
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        telegram = Telegram(GroupAddress("1/2/3"), payload=DPTArray((23, 24)))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(notification.process(telegram))

    def test_process_wrong_payload(self):
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        telegram = Telegram(GroupAddress("1/2/3"), payload=DPTBinary(1))
        with self.assertRaises(CouldNotParseTelegram):
            self.loop.run_until_complete(notification.process(telegram))

    #
    # TEST SET MESSAGE
    #
    def test_set(self):
        """Test notificationing off notification."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        self.loop.run_until_complete(notification.set("Ein Prosit!"))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress("1/2/3"),
                payload=DPTArray(DPTString().to_knx("Ein Prosit!")),
            ),
        )
        # test if message longer than 14 chars gets cropped
        self.loop.run_until_complete(notification.set("This is too long."))

        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress("1/2/3"),
                payload=DPTArray(DPTString().to_knx("This is too lo")),
            ),
        )

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        self.loop.run_until_complete(notification.do("message:Ein Prosit!"))
        self.loop.run_until_complete(xknx.devices.process(xknx.telegrams.get_nowait()))
        self.assertEqual(notification.message, "Ein Prosit!")

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(notification.do("execute"))
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "Warning"
            )
        self.assertEqual(xknx.telegrams.qsize(), 0)

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        notification = Notification(
            xknx, "Warning", group_address="1/2/3", group_address_state="1/2/4"
        )
        self.assertTrue(notification.has_group_address(GroupAddress("1/2/3")))
        self.assertTrue(notification.has_group_address(GroupAddress("1/2/4")))
        self.assertFalse(notification.has_group_address(GroupAddress("2/2/2")))
