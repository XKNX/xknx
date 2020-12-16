"""Unit test for telegram received callback."""
import asyncio
import unittest
from unittest.mock import MagicMock, Mock, patch

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError, CouldNotParseTelegram
from xknx.telegram import AddressFilter, GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite


class AsyncMock(MagicMock):
    """Async Mock."""

    # pylint: disable=invalid-overridden-method
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


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
        xknx = XKNX()

        telegram_in = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        self.loop.run_until_complete(xknx.telegram_queue.start())

        self.assertFalse(xknx.telegram_queue._consumer_task.done())
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
        self.assertTrue(xknx.telegram_queue._consumer_task.done())

    @patch("asyncio.sleep")
    def test_rate_limit(self, async_sleep_mock):
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
            payload=GroupValueWrite(DPTBinary(1)),
        )

        telegram_out = Telegram(
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

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
        xknx = XKNX()
        async_telegram_received_cb = AsyncMock()

        xknx.telegram_queue.register_telegram_received_cb(async_telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_incoming(telegram)
        )
        async_telegram_received_cb.assert_called_once_with(telegram)

    #
    # TEST UNREGISTER
    #
    def test_unregister(self):
        """Test telegram_received_callback after state of switch was changed."""
        # pylint: disable=no-self-use
        xknx = XKNX()
        async_telegram_received_callback = AsyncMock()

        callback = xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_callback
        )
        xknx.telegram_queue.unregister_telegram_received_cb(callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_incoming(telegram)
        )
        async_telegram_received_callback.assert_not_called()

    #
    # TEST PROCESS
    #
    @patch("xknx.devices.Devices.devices_by_group_address")
    def test_process_to_device(self, devices_by_ga_mock):
        """Test process_telegram_incoming for forwarding telegram to a device."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        test_device = Mock()
        async_device_process = asyncio.Future()
        async_device_process.set_result(None)
        test_device.process.return_value = async_device_process

        devices_by_ga_mock.return_value = [test_device]

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_incoming(telegram)
        )

        devices_by_ga_mock.assert_called_once_with(GroupAddress("1/2/3"))
        test_device.process.assert_called_once_with(telegram)

    @patch("xknx.devices.Devices.process", new_callable=AsyncMock)
    def test_process_to_callback(self, devices_process):
        """Test process_telegram_incoming with callback."""
        # pylint: disable=no-self-use
        xknx = XKNX()
        async_telegram_received_callback = AsyncMock()

        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_callback
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_incoming(telegram)
        )
        async_telegram_received_callback.assert_called_once_with(telegram)
        devices_process.assert_called_once_with(telegram)

    @patch("xknx.io.KNXIPInterface")
    def test_outgoing(self, if_mock):
        """Test outgoing telegrams in telegram queue."""
        xknx = XKNX()

        async_if_send_telegram = asyncio.Future()
        async_if_send_telegram.set_result(None)
        if_mock.send_telegram.return_value = async_if_send_telegram

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        # log a warning if there is no KNXIP interface instanciated
        with self.assertRaises(CommunicationError):
            self.loop.run_until_complete(
                xknx.telegram_queue.process_telegram_outgoing(telegram)
            )
        if_mock.send_telegram.assert_not_called()

        # if we have an interface send the telegram
        xknx.knxip_interface = if_mock
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_outgoing(telegram)
        )
        if_mock.send_telegram.assert_called_once_with(telegram)

    @patch("logging.Logger.error")
    @patch("xknx.core.TelegramQueue.process_telegram_incoming", new_callable=MagicMock)
    def test_process_exception(self, process_tg_in_mock, logging_error_mock):
        """Test process_telegram exception handling."""
        # pylint: disable=no-self-use
        xknx = XKNX()

        async def process_exception():
            raise CouldNotParseTelegram(
                "Something went wrong when receiving the telegram." ""
            )

        process_tg_in_mock.return_value = asyncio.ensure_future(process_exception())

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        xknx.telegrams.put_nowait(telegram)
        self.loop.run_until_complete(xknx.telegram_queue._process_all_telegrams())

        logging_error_mock.assert_called_once_with(
            "Error while processing telegram %s",
            CouldNotParseTelegram(
                "Something went wrong when receiving the telegram." ""
            ),
        )

    @patch("xknx.core.TelegramQueue.process_telegram_outgoing", new_callable=AsyncMock)
    @patch("xknx.core.TelegramQueue.process_telegram_incoming", new_callable=AsyncMock)
    def test_process_all_telegrams(
        self, process_telegram_incoming_mock, process_telegram_outgoing_mock
    ):
        """Test _process_all_telegrams for clearing the queue."""
        xknx = XKNX()

        telegram_in = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram_out = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_out)
        res = self.loop.run_until_complete(xknx.telegram_queue._process_all_telegrams())

        self.assertIsNone(res)
        process_telegram_incoming_mock.assert_called_once()
        process_telegram_outgoing_mock.assert_called_once()

    #
    # TEST NO FILTERS
    #
    def test_callback_no_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        async_telegram_received_callback = AsyncMock()

        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_callback
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        xknx.telegrams.put_nowait(telegram)
        self.loop.run_until_complete(xknx.telegram_queue._process_all_telegrams())

        async_telegram_received_callback.assert_called_with(telegram)

    #
    # TEST POSITIVE FILTERS
    #
    def test_callback_positive_address_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        async_telegram_received_callback = AsyncMock()

        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_callback,
            address_filters=[AddressFilter("2/4-8/*"), AddressFilter("1/2/-8")],
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        xknx.telegrams.put_nowait(telegram)
        self.loop.run_until_complete(xknx.telegram_queue._process_all_telegrams())

        async_telegram_received_callback.assert_called_with(telegram)

    #
    # TEST NEGATIVE FILTERS
    #
    def test_callback_negative_address_filters(self):
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        async_telegram_received_callback = AsyncMock()

        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_callback,
            address_filters=[AddressFilter("2/4-8/*"), AddressFilter("1/2/8-")],
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        xknx.telegrams.put_nowait(telegram)
        self.loop.run_until_complete(xknx.telegram_queue._process_all_telegrams())

        async_telegram_received_callback.assert_not_called()

    def test_callback_group_addresses(self):
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        async_telegram_received_cb_one = AsyncMock()
        async_telegram_received_cb_two = AsyncMock()

        callback_one = xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb_one,
            address_filters=[],
            group_addresses=[GroupAddress("1/2/3")],
        )
        callback_two = xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb_two, address_filters=[], group_addresses=[]
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_incoming(telegram)
        )
        async_telegram_received_cb_one.assert_called_once_with(telegram)
        async_telegram_received_cb_two.assert_not_called()

        async_telegram_received_cb_one.reset_mock()
        # modify the filters - add/remove a GroupAddress
        callback_one.group_addresses.remove(GroupAddress("1/2/3"))
        callback_two.group_addresses.append(GroupAddress("1/2/3"))
        self.loop.run_until_complete(
            xknx.telegram_queue.process_telegram_incoming(telegram)
        )
        async_telegram_received_cb_one.assert_not_called()
        async_telegram_received_cb_two.assert_called_once_with(telegram)
