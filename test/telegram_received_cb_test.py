"""Unit test for telegram received callback."""
import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.knx import (GroupAddress, AddressFilter, DPTBinary, Telegram,
                      TelegramDirection)


class TestTelegramReceivedCallback(unittest.TestCase):
    """Test class for telegram received callbacks."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # TEST NO FILTERS
    #
    def test_no_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        @asyncio.coroutine
        def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb)

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        telegram_received_callback.assert_called_with(telegram)

    #
    # TEST POSITIVE FILTERS
    #
    def test_positive_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        @asyncio.coroutine
        def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb,
            [AddressFilter("2/4-8/*"), AddressFilter("1/2/-8")])

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        telegram_received_callback.assert_called_with(telegram)

    #
    # TEST NEGATIVE FILTERS
    #
    def test_negative_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        @asyncio.coroutine
        def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb,
            [AddressFilter("2/4-8/*"), AddressFilter("1/2/8-")])

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        telegram_received_callback.assert_not_called()

    #
    # TEST UNREGISTER
    #
    def test_unregister(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        @asyncio.coroutine
        def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        callback = xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb)
        xknx.telegram_queue.unregister_telegram_received_cb(callback)

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        telegram_received_callback.assert_not_called()
