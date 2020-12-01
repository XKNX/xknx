"""Unit test for Telegram objects."""
import unittest

from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


class TestTelegram(unittest.TestCase):
    """Test class for Telegram objects."""

    #
    # EQUALITY
    #
    def test_telegram_equal(self):
        """Test equals operator."""
        self.assertEqual(
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()),
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()),
        )

    def test_telegram_not_equal(self):
        """Test not equals operator."""
        self.assertNotEqual(
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()),
            Telegram(GroupAddress("1/2/4"), payload=GroupValueRead()),
        )
        self.assertNotEqual(
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()),
            Telegram(GroupAddress("1/2/3"), payload=GroupValueWrite(DPTBinary(1))),
        )
        self.assertNotEqual(
            Telegram(GroupAddress("1/2/3"), payload=GroupValueRead()),
            Telegram(
                GroupAddress("1/2/3"),
                TelegramDirection.INCOMING,
                payload=GroupValueRead(),
            ),
        )
