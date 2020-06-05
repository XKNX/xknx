"""Unit test for telegram received callback."""
import asyncio
from unittest.mock import Mock, patch
import pytest

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import (
    AddressFilter, GroupAddress, Telegram, TelegramDirection)

from xknx._test import Testcase, CoroMock

class TestTelegramQueue(Testcase):
    """Test class for telegram queue."""

    #
    # TEST START, RUN, STOP
    #
    @pytest.mark.asyncio
    async def test_start(self):
        """Test start, run and stop."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_in = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        async with xknx.telegram_queue.run_test():
            self.assertFalse(xknx.telegram_queue.queue_stopped.is_set())
            # queue shall now consume telegrams from xknx.telegrams
            self.assertEqual(xknx.telegrams.qsize(), 0)
            await xknx.telegrams.put(telegram_in)
            await xknx.telegrams.put(telegram_in)
            self.assertEqual(xknx.telegrams.qsize(), 2)
            # wait until telegrams are consumed
            while xknx.telegrams.qsize():
                await asyncio.sleep(0.01)
        self.assertTrue(xknx.telegram_queue.queue_stopped.is_set())

    @pytest.mark.skip
    @patch('asyncio.sleep')
    @pytest.mark.asyncio
    async def test_rate_limit(self, async_sleep_mock):
        """Test rate limit."""
        # pylint: disable=no-self-use
        async def async_none():
            return None
        async_sleep_mock.return_value = asyncio.ensure_future(async_none())

        xknx = XKNX()
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

        async with xknx.telegram_queue.run_test():

            # no sleep for incoming telegrams
            await xknx.telegrams.put(telegram_in)
            await xknx.telegrams.put(telegram_in)
            while xknx.telegrams.qsize():
                await asyncio.sleep(0.01)
            self.assertEqual(async_sleep_mock.call_count, 0)
            # sleep for outgoing telegrams
            await xknx.telegrams.put(telegram_out)
            await xknx.telegrams.put(telegram_out)
            while xknx.telegrams.qsize():
                await asyncio.sleep(0.01)
            self.assertEqual(async_sleep_mock.call_count, 2)
            async_sleep_mock.assert_called_with(sleep_time)

    #
    # TEST REGISTER
    #
    @pytest.mark.asyncio
    async def test_register(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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
        await xknx.telegram_queue.process_telegram(telegram)
        telegram_received_callback.assert_called_once_with(telegram)

    #
    # TEST UNREGISTER
    #
    @pytest.mark.asyncio
    async def test_unregister(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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
        await xknx.telegram_queue.process_telegram(telegram)
        telegram_received_callback.assert_not_called()

    #
    # TEST PROCESS
    #
    @patch('xknx.devices.Devices.devices_by_group_address')
    @pytest.mark.asyncio
    async def test_process_to_device(self, devices_by_ga_mock):
        """Test process_telegram for forwarding telegram to a device."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        test_device = Mock()
        async_device_process = asyncio.Future()
        async_device_process.set_result(None)
        test_device.process.return_value = async_device_process

        devices_by_ga_mock.return_value = [test_device]

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegram_queue.process_telegram(telegram)

        devices_by_ga_mock.assert_called_once_with(GroupAddress("1/2/3"))
        test_device.process.assert_called_once_with(telegram)

    @patch('xknx.devices.Devices.devices_by_group_address')
    @pytest.mark.asyncio
    async def test_process_to_callback(self, devices_by_ga_mock):
        """Test process_telegram for returning after processing callback."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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
        await xknx.telegram_queue.process_telegram(telegram)
        telegram_received_callback.assert_called_once_with(telegram)
        devices_by_ga_mock.assert_not_called()

    @patch('xknx.io.KNXIPInterface')
    @patch('logging.Logger.warning')
    @pytest.mark.asyncio
    async def test_outgoing(self, logger_warning_mock, if_mock):
        """Test outgoing telegrams in telegram queue."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        async_if_send_telegram = asyncio.Future()
        async_if_send_telegram.set_result(None)
        if_mock.send_telegram.return_value = async_if_send_telegram

        telegram = Telegram(
            direction=TelegramDirection.OUTGOING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        # log a warning if there is no KNXIP interface instanciated
        await xknx.telegram_queue.process_telegram(telegram)
        logger_warning_mock.assert_called_once_with(
            "No KNXIP interface defined")
        if_mock.send_telegram.assert_not_called()

        # if we have an interface send the telegram
        xknx.knxip_interface = if_mock
        await xknx.telegram_queue.process_telegram(telegram)
        if_mock.send_telegram.assert_called_once_with(telegram)

    @patch('logging.Logger.error')
    @patch('xknx.core.TelegramQueue.process_telegram_incoming',
            new_callable=CoroMock)
    @pytest.mark.asyncio
    async def test_process_exception(self, process_tg_in_mock, logging_error_mock):
        """Test process_telegram exception handling."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        def process_exception(x):
            raise CouldNotParseTelegram("Something went wrong when receiving the telegram.")
        process_tg_in_mock.side_effect = process_exception

        telegram = Telegram(
            direction=TelegramDirection.INCOMING,
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        await xknx.telegram_queue.process_telegram(telegram)
        logging_error_mock.assert_called_once_with(
            "Error while processing telegram %s",
            CouldNotParseTelegram("Something went wrong when receiving the telegram."))

    @patch('xknx.core.TelegramQueue.process_telegram')
    @pytest.mark.asyncio
    async def test_process_all_telegrams(self, process_telegram_mock):
        """Test process_all_telegrams for clearing the queue."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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

        await xknx.telegrams.put(telegram_in)
        await xknx.telegrams.put(telegram_out)
        res = await xknx.telegram_queue.process_all_telegrams()

        self.assertIsNone(res)
        self.assertEqual(process_telegram_mock.call_count, 2)

    #
    # TEST NO FILTERS
    #
    @pytest.mark.asyncio
    async def test_no_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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
        await xknx.telegram_queue.process_telegram(telegram)
        telegram_received_callback.assert_called_with(telegram)

    #
    # TEST POSITIVE FILTERS
    #
    @pytest.mark.asyncio
    async def test_positive_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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
        await xknx.telegram_queue.process_telegram(telegram)
        telegram_received_callback.assert_called_with(telegram)

    #
    # TEST NEGATIVE FILTERS
    #
    @pytest.mark.asyncio
    async def test_negative_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

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
        await xknx.telegram_queue.process_telegram(telegram)
        telegram_received_callback.assert_not_called()
