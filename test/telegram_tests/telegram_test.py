"""Unit test for Telegram objects."""
import unittest

from xknx.telegram import (
    GroupAddress, Telegram, TelegramDirection, TelegramType)


class TestTelegram(unittest.TestCase):
    """Test class for Telegram objects."""

    #
    # EQUALITY
    #
    def test_telegram_equal(self):
        """Test equals operator."""
        self.assertEqual(
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ),
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    def test_telegram_not_equal(self):
        """Test not equals operator."""
        self.assertNotEqual(
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ),
            Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))
        self.assertNotEqual(
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ),
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_WRITE))
        self.assertNotEqual(
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ),
            Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ,
                     TelegramDirection.INCOMING))
