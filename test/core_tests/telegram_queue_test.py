"""Unit test for telegram received callback."""
import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import (
    AddressFilter, GroupAddress, Telegram, TelegramDirection)


class TestTelegramQueue(unittest.TestCase):
    """Test class for telegram queue."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # TEST START, RUN, STOP
    #
    def test_start(self):
        """Test start, run and stop."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_in = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        self.loop.run_until_complete(xknx.telegram_queue.start())

        self.assertFalse(xknx.telegram_queue.queue_stopped.is_set())
        # queue shall now consume telegrams from xknx.telegrams
        self.assertEqual(xknx.telegrams.qsize(), 0)
        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_in)
        self.assertEqual(xknx.telegrams.qsize(), 2)
        # wait until telegrams are consumed
        self.loop.run_until_complete(xknx.telegrams.join())
        self.assertEqual(xknx.telegrams.qsize(), 0)
        self.loop.run_until_complete(xknx.telegrams.join())
        self.assertEqual(xknx.telegrams.qsize(), 0)
        # stop run() task with stop()
        self.loop.run_until_complete(xknx.telegram_queue.stop())
        self.assertTrue(xknx.telegram_queue.queue_stopped.is_set())

    @patch('asyncio.sleep')
    def test_rate_limit(self, async_sleep_mock):
        """Test rate limit."""
        # pylint: disable=no-self-use
        async def async_none():
            return None
        async_sleep_mock.return_value = asyncio.ensure_future(async_none())

        xknx = XKNX(loop=self.loop)
        xknx.rate_limit = 20  # 50 ms per outgoing telegram
        sleep_time = 0.05  # 1 / 20

        telegram_in = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        telegram_out = Telegram(
            direction=TelegramDirection.OUTGOING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        self.loop.run_until_complete(xknx.telegram_queue.start())

        # no sleep for incoming telegrams
        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_in)
        self.loop.run_until_complete(xknx.telegrams.join())
        self.assertEqual(async_sleep_mock.call_count, 0)
        # sleep for outgoing telegrams
        xknx.telegrams.put_nowait(telegram_out)
        xknx.telegrams.put_nowait(telegram_out)
        self.loop.run_until_complete(xknx.telegrams.join())
        self.assertEqual(async_sleep_mock.call_count, 2)
        async_sleep_mock.assert_called_with(sleep_time)

        self.loop.run_until_complete(xknx.telegram_queue.stop())

    #
    # TEST REGISTER
    #
    def test_register(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
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
        telegram_received_callback.assert_called_once_with(telegram)

    #
    # TEST UNREGISTER
    #
    def test_unregister(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
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

    #
    # TEST PROCESS
    #
    @patch('xknx.devices.Devices.devices_by_group_address')
    def test_process_to_device(self, devices_by_ga_mock):
        """Test process_telegram for forwarding telegram to a device."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        test_device = Mock()
        async_device_process = asyncio.Future()
        async_device_process.set_result(None)
        test_device.process.return_value = async_device_process

        devices_by_ga_mock.return_value = [test_device]

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))

        devices_by_ga_mock.assert_called_once_with(GroupAddress("1/2/3"))
        test_device.process.assert_called_once_with(telegram)

    @patch('xknx.devices.Devices.devices_by_group_address')
    def test_process_to_callback(self, devices_by_ga_mock):
        """Test process_telegram for returning after processing callback."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback. Returning 'True'."""
            telegram_received_callback(device)
            return True

        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb)

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        telegram_received_callback.assert_called_once_with(telegram)
        devices_by_ga_mock.assert_not_called()

    @patch('xknx.io.KNXIPInterface')
    @patch('logging.Logger.warning')
    def test_outgoing(self, logger_warning_mock, if_mock):
        """Test outgoing telegrams in telegram queue."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        async_if_send_telegram = asyncio.Future()
        async_if_send_telegram.set_result(None)
        if_mock.send_telegram.return_value = async_if_send_telegram

        telegram = Telegram(
            direction=TelegramDirection.OUTGOING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        # log a warning if there is no KNXIP interface instanciated
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        logger_warning_mock.assert_called_once_with(
            "No KNXIP interface defined")
        if_mock.send_telegram.assert_not_called()

        # if we have an interface send the telegram
        xknx.knxip_interface = if_mock
        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        if_mock.send_telegram.assert_called_once_with(telegram)

    @patch('logging.Logger.error')
    @patch('xknx.core.TelegramQueue.process_telegram_incoming')
    def test_process_exception(self, process_tg_in_mock, logging_error_mock):
        """Test process_telegram exception handling."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        async def process_exception():
            raise CouldNotParseTelegram("Something went wrong when receiving the telegram.""")
        process_tg_in_mock.return_value = asyncio.ensure_future(process_exception())

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_telegram(telegram)))
        logging_error_mock.assert_called_once_with(
            "Error while processing telegram %s",
            CouldNotParseTelegram("Something went wrong when receiving the telegram."""))

    @patch('xknx.core.TelegramQueue.process_telegram')
    def test_process_all_telegrams(self, process_telegram_mock):
        """Test process_all_telegrams for clearing the queue."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        async_process_mock = asyncio.Future()
        async_process_mock.set_result(None)
        process_telegram_mock.return_value = async_process_mock

        telegram_in = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        telegram_out = Telegram(
            direction=TelegramDirection.OUTGOING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_out)
        res = self.loop.run_until_complete(asyncio.Task(
            xknx.telegram_queue.process_all_telegrams()))

        self.assertIsNone(res)
        self.assertEqual(process_telegram_mock.call_count, 2)

    #
    # TEST NO FILTERS
    #
    def test_no_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
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

        async def async_telegram_received_cb(device):
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

        async def async_telegram_received_cb(device):
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
