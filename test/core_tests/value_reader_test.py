"""Unit test for value reader."""
import asyncio
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.core import ValueReader
from xknx.dpt import DPTBinary
from xknx.telegram import (
    GroupAddress, Telegram, TelegramDirection, TelegramType)


class TestValueReader(unittest.TestCase):
    """Test class for value reader."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    @patch('xknx.core.ValueReader.timeout')
    def test_value_reader_read_success(self, timeout_mock):
        """Test value reader: successfull read."""
        xknx = XKNX(loop=self.loop)
        test_group_address = GroupAddress("0/0/0")
        response_telegram = Telegram(group_address=test_group_address,
                                     telegramtype=TelegramType.GROUP_RESPONSE,
                                     direction=TelegramDirection.INCOMING,
                                     payload=DPTBinary(1))

        value_reader = ValueReader(xknx, test_group_address)
        # Create a task for read() (3.5 compatible)
        read_task = asyncio.ensure_future(value_reader.read())
        # receive the response
        self.loop.run_until_complete(value_reader.telegram_received(response_telegram))
        # and yield the result
        successfull_read = self.loop.run_until_complete(asyncio.gather(read_task))[0]

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        self.assertEqual(xknx.telegrams.qsize(), 1)
        # Callback was removed again
        self.assertEqual(xknx.telegram_queue.telegram_received_cbs,
                         [])
        # Timeout handle was cancelled (cancelled method requires Python 3.7)
        event_has_cancelled = getattr(value_reader.timeout_handle, "cancelled", None)
        if callable(event_has_cancelled):
            self.assertTrue(value_reader.timeout_handle.cancelled())
        # timeout() was never called because there was no timeout
        timeout_mock.assert_not_called()
        # Telegram was received
        self.assertEqual(value_reader.received_telegram,
                         response_telegram)
        # Successfull read() returns the telegram
        self.assertEqual(successfull_read,
                         response_telegram)

    @patch('logging.Logger.warning')
    def test_value_reader_read_timeout(self, logger_warning_mock):
        """Test value reader: read timeout."""
        xknx = XKNX(loop=self.loop)
        value_reader = ValueReader(xknx, GroupAddress('0/0/0'), timeout_in_seconds=0)

        timed_out_read = self.loop.run_until_complete(value_reader.read())

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        self.assertEqual(xknx.telegrams.qsize(), 1)
        # Warning was logged
        logger_warning_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time to GroupValueRead request for: %s", GroupAddress('0/0/0'))
        # Callback was removed again
        self.assertEqual(xknx.telegram_queue.telegram_received_cbs,
                         [])
        # Timeout handle was cancelled (cancelled method requires Python 3.7)
        event_has_cancelled = getattr(value_reader.timeout_handle, "cancelled", None)
        if callable(event_has_cancelled):
            self.assertTrue(value_reader.timeout_handle.cancelled())
        # No telegram was received
        self.assertIsNone(value_reader.received_telegram)
        # Unsuccessfull read() returns None
        self.assertIsNone(timed_out_read)

    def test_value_reader_send_group_read(self):
        """Test value reader: send_group_read."""
        xknx = XKNX(loop=self.loop)
        value_reader = ValueReader(xknx, GroupAddress('0/0/0'))

        self.loop.run_until_complete(value_reader.send_group_read())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(group_address=GroupAddress('0/0/0'),
                                  telegramtype=TelegramType.GROUP_READ))

    def test_value_reader_telegram_received(self):
        """Test value reader: telegram_received."""
        xknx = XKNX(loop=self.loop)
        test_group_address = GroupAddress("0/0/0")
        expected_telegram_1 = Telegram(group_address=test_group_address,
                                       telegramtype=TelegramType.GROUP_RESPONSE,
                                       direction=TelegramDirection.INCOMING,
                                       payload=DPTBinary(1))
        expected_telegram_2 = Telegram(group_address=test_group_address,
                                       telegramtype=TelegramType.GROUP_WRITE,
                                       direction=TelegramDirection.INCOMING,
                                       payload=DPTBinary(1))
        telegram_wrong_address = Telegram(group_address=GroupAddress("0/0/1"),
                                          telegramtype=TelegramType.GROUP_RESPONSE,
                                          direction=TelegramDirection.INCOMING,
                                          payload=DPTBinary(1))
        telegram_wrong_type = Telegram(group_address=test_group_address,
                                       telegramtype=TelegramType.GROUP_READ,
                                       direction=TelegramDirection.INCOMING,
                                       payload=DPTBinary(1))

        value_reader = ValueReader(xknx, test_group_address)

        def async_telegram_received(test_telegram):
            return self.loop.run_until_complete(value_reader.telegram_received(test_telegram))

        self.assertFalse(async_telegram_received(telegram_wrong_address))
        self.assertFalse(async_telegram_received(telegram_wrong_type))
        self.assertIsNone(value_reader.received_telegram)

        self.assertTrue(async_telegram_received(expected_telegram_1))
        self.assertEqual(value_reader.received_telegram, expected_telegram_1)

        self.assertTrue(async_telegram_received(expected_telegram_2))
        self.assertEqual(value_reader.received_telegram, expected_telegram_2)
