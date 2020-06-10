"""Unit test for telegram received callback."""
import anyio
from unittest.mock import Mock, patch
import pytest

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.devices import Device
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import AddressFilter, GroupAddress, Telegram

from xknx._test import Testcase, AsyncMock

class TestTelegramQueueIn(Testcase):
    """Test class for the incoming telegram queue."""

    #
    # TEST START, RUN, STOP
    #
    @pytest.mark.anyio
    async def test_start(self):
        """Test start, run and stop."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_in = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        async with xknx.telegrams_in.run_test():
            self.assertFalse(xknx.telegrams_in.queue_stopped.is_set())
            # queue shall now consume telegrams from xknx.telegrams_in
            self.assertEqual(xknx.telegrams_in.qsize(), 0)
            await xknx.telegrams_in.put(telegram_in)
            await xknx.telegrams_in.put(telegram_in)
            # "put" might actually run the consumer immediately
            # self.assertEqual(xknx.telegrams_in.qsize(), 2)
            # wait until telegrams are consumed
            while xknx.telegrams_in.qsize():
                await anyio.sleep(0.01)
        self.assertTrue(xknx.telegrams_in.queue_stopped.is_set())

    @pytest.mark.skip
    @patch('anyio.sleep', new_callable=AsyncMock)
    @pytest.mark.anyio
    async def test_rate_limit(self, async_sleep_mock):
        """Test rate limit."""
        xknx = XKNX()
        xknx.rate_limit = 20  # 50 ms per outgoing telegram
        sleep_time = 0.05  # 1 / 20

        telegram_in = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        telegram_out = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        async with xknx.telegrams_in.run_test():

            # no sleep for incoming telegrams
            await xknx.telegrams_in.put(telegram_in)
            await xknx.telegrams_in.put(telegram_in)
            while xknx.telegrams_in.qsize():
                await anyio.sleep(0.01)
            self.assertEqual(async_sleep_mock.call_count, 0)
            # sleep for outgoing telegrams
            await xknx.telegrams_out.put(telegram_out)
            await xknx.telegrams_out.put(telegram_out)
            while xknx.telegrams_in.qsize():
                await anyio.sleep(0.01)
            self.assertEqual(async_sleep_mock.call_count, 2)
            async_sleep_mock.assert_called_with(sleep_time)

    #
    # TEST REGISTER
    #
    @pytest.mark.anyio
    async def test_register(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegrams_in.register_telegram_cb(
            async_telegram_received_cb)

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)
        telegram_received_callback.assert_called_once_with(telegram)

    @pytest.mark.anyio
    async def test_receiver(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        # No callback or similar nonlinearity required.
        with xknx.telegrams_in.receiver() as recv:
            telegram = Telegram(
                payload=DPTBinary(1),
                group_address=GroupAddress("1/2/3"))
            await xknx.telegrams_in.process_telegram(telegram)
            async for msg in recv:
                assert msg is telegram
                break

    #
    # TEST UNREGISTER
    #
    @pytest.mark.anyio
    async def test_unregister(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        callback = xknx.telegrams_in.register_telegram_cb(
            async_telegram_received_cb)
        xknx.telegrams_in.unregister_telegram_cb(callback)

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)
        telegram_received_callback.assert_not_called()

    #
    # TEST PROCESS
    #
    @patch('xknx.devices.Devices.devices_by_group_address')
    @pytest.mark.anyio
    async def test_process_to_device(self, devices_by_ga_mock):
        """Test process_telegram for forwarding telegram to a device."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        test_device = AsyncMock()
        devices_by_ga_mock.return_value = [test_device]

        device = Device(xknx, 'TestDevice')
        xknx.devices.add(device)

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)

        devices_by_ga_mock.assert_called_once_with(GroupAddress("1/2/3"))
        test_device.process.assert_called_once_with(telegram)

    #
    # TEST PROCESS
    #
    @patch('xknx.devices.Devices.devices_by_group_address')
    @pytest.mark.anyio
    async def test_process_to_device_empty(self, devices_by_ga_mock):
        """Test process_telegram for forwarding telegram to a device."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        test_device = AsyncMock()
        devices_by_ga_mock.return_value = [test_device]

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)

        devices_by_ga_mock.assert_not_called()
        test_device.process.assert_not_called()

    @patch('xknx.devices.Devices.devices_by_group_address')
    @pytest.mark.anyio
    async def test_process_to_callback(self, devices_by_ga_mock):
        """Test process_telegram for returning after processing callback."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback. Returning 'True'."""
            telegram_received_callback(device)
            return True

        xknx.telegrams_in.register_telegram_cb(
            async_telegram_received_cb)

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)
        telegram_received_callback.assert_called_once_with(telegram)
        devices_by_ga_mock.assert_not_called()

    @patch('xknx.io.KNXIPInterface', new_callable=AsyncMock)
    @patch('logging.Logger.warning')
    @pytest.mark.anyio
    async def test_outgoing(self, logger_warning_mock, if_mock):
        """Test outgoing telegrams in telegrams_inqueue."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        async with xknx.telegrams_out.run_test():
            # log a warning if there is no KNXIP interface instanciated
            await xknx.telegrams_out.process_telegram(telegram)

            logger_warning_mock.assert_called_once_with(
                "No KNXIP interface defined")
            if_mock.send_telegram.assert_not_called()

            # if we have an interface send the telegram
            xknx.knxip_interface = if_mock
            await xknx.telegrams_out.process_telegram(telegram)
            if_mock.send_telegram.assert_called_once_with(telegram)

    @patch('logging.Logger.error')
    @patch('xknx.core.TelegramQueueIn.process_telegram',
            new_callable=AsyncMock)
    @pytest.mark.anyio
    async def test_process_exception(self, process_tg_in_mock, logging_error_mock):
        """Test process_telegram exception handling."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        async def process_exception(_=None):
            raise CouldNotParseTelegram("Something went wrong when receiving the telegram.")
        process_tg_in_mock.side_effect = process_exception

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        with pytest.raises(CouldNotParseTelegram):
            await xknx.telegrams_in.process_telegram(telegram)
        logging_error_mock.assert_not_called()

    @patch('xknx.core.TelegramQueue.process_telegram', new_callable=AsyncMock)
    @pytest.mark.anyio
    async def test_process_all_telegrams(self, process_telegram_mock):
        """Test process_all_telegrams for clearing the queue."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_in = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        telegram_out = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))

        async with anyio.create_task_group() as tg:
            xknx.task_group = tg
            await xknx.telegrams_in.start()
            await xknx.telegrams_out.start()

            await xknx.telegrams_in.put(telegram_in)
            await xknx.telegrams_out.put(telegram_out)
            await xknx.telegrams_in.process_all_telegrams()
            await xknx.telegrams_out.process_all_telegrams()
            await tg.cancel_scope.cancel()

        self.assertEqual(process_telegram_mock.call_count, 2)

    #
    # TEST NO FILTERS
    #
    @pytest.mark.anyio
    async def test_no_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegrams_in.register_telegram_cb(
            async_telegram_received_cb)

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)
        telegram_received_callback.assert_called_with(telegram)

    #
    # TEST POSITIVE FILTERS
    #
    @pytest.mark.anyio
    async def test_positive_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegrams_in.register_telegram_cb(
            async_telegram_received_cb,
            [AddressFilter("2/4-8/*"), AddressFilter("1/2/-8")])

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)
        telegram_received_callback.assert_called_with(telegram)

    #
    # TEST NEGATIVE FILTERS
    #
    @pytest.mark.anyio
    async def test_negative_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        telegram_received_callback = Mock()

        async def async_telegram_received_cb(device):
            """Async callback."""
            telegram_received_callback(device)
        xknx.telegrams_in.register_telegram_cb(
            async_telegram_received_cb,
            [AddressFilter("2/4-8/*"), AddressFilter("1/2/8-")])

        telegram = Telegram(
            payload=DPTBinary(1),
            group_address=GroupAddress("1/2/3"))
        await xknx.telegrams_in.process_telegram(telegram)
        telegram_received_callback.assert_not_called()
