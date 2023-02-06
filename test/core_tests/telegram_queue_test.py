"""Unit test for telegram received callback."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError, CouldNotParseTelegram
from xknx.telegram import AddressFilter, Telegram, TelegramDirection
from xknx.telegram.address import GroupAddress, InternalGroupAddress
from xknx.telegram.apci import GroupValueWrite


class TestTelegramQueue:
    """Test class for telegram queue."""

    #
    # TEST START, RUN, STOP
    #
    async def test_start(self):
        """Test start, run and stop."""

        xknx = XKNX()

        telegram_in = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await xknx.telegram_queue.start()

        assert not xknx.telegram_queue._consumer_task.done()
        # queue shall now consume telegrams from xknx.telegrams
        assert xknx.telegrams.qsize() == 0
        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_in)
        assert xknx.telegrams.qsize() == 2
        # wait until telegrams are consumed
        await xknx.telegrams.join()
        assert xknx.telegrams.qsize() == 0
        await xknx.telegrams.join()
        assert xknx.telegrams.qsize() == 0
        # stop run() task with stop()
        await xknx.telegram_queue.stop()
        assert xknx.telegram_queue._consumer_task.done()

    @patch("asyncio.sleep", new_callable=AsyncMock)
    async def test_rate_limit(self, async_sleep_mock):
        """Test rate limit."""
        xknx = XKNX(
            rate_limit=20,  # 50 ms per outgoing telegram
        )
        sleep_time = 0.05  # 1 / 20

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
        telegram_internal = Telegram(
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
            destination_address=InternalGroupAddress("i-test"),
        )
        await xknx.telegram_queue.start()

        # no sleep for incoming telegrams
        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_in)
        await xknx.telegrams.join()
        assert async_sleep_mock.call_count == 0

        # sleep for outgoing telegrams
        xknx.telegrams.put_nowait(telegram_out)
        xknx.telegrams.put_nowait(telegram_out)
        await xknx.telegrams.join()
        assert async_sleep_mock.call_count == 2
        async_sleep_mock.assert_called_with(sleep_time)

        async_sleep_mock.reset_mock()
        # no sleep for internal group address telegrams
        xknx.telegrams.put_nowait(telegram_internal)
        xknx.telegrams.put_nowait(telegram_internal)
        await xknx.telegrams.join()
        async_sleep_mock.assert_not_called()

        await xknx.telegram_queue.stop()

    #
    # TEST REGISTER
    #
    async def test_register(self):
        """Test telegram_received_callback after state of switch was changed."""

        xknx = XKNX()
        async_telegram_received_cb = AsyncMock()
        xknx.telegram_queue.register_telegram_received_cb(async_telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        async_telegram_received_cb.assert_called_once_with(telegram)

    async def test_register_with_outgoing_telegrams(self):
        """Test telegram_received_callback with outgoing telegrams."""

        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()
        async_telegram_received_cb = AsyncMock()
        xknx.telegram_queue.register_telegram_received_cb(
            async_telegram_received_cb, None, None, True
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await xknx.telegram_queue.process_telegram_outgoing(telegram)
        async_telegram_received_cb.assert_called_once_with(telegram)

    async def test_register_with_outgoing_telegrams_does_not_trigger(self):
        """Test telegram_received_callback with outgoing telegrams."""

        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()
        async_telegram_received_cb = AsyncMock()
        xknx.telegram_queue.register_telegram_received_cb(async_telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await xknx.telegram_queue.process_telegram_outgoing(telegram)
        async_telegram_received_cb.assert_not_called()

    #
    # TEST UNREGISTER
    #
    async def test_unregister(self):
        """Test telegram_received_callback after state of switch was changed."""

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
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        async_telegram_received_callback.assert_not_called()

    #
    # TEST PROCESS
    #
    @patch("xknx.devices.Devices.devices_by_group_address")
    async def test_process_to_device(self, devices_by_ga_mock):
        """Test process_telegram_incoming for forwarding telegram to a device."""

        xknx = XKNX()
        test_device = AsyncMock()
        devices_by_ga_mock.return_value = [test_device]

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        devices_by_ga_mock.assert_called_once_with(GroupAddress("1/2/3"))
        test_device.process.assert_called_once_with(telegram)

    @patch("xknx.devices.Devices.process", new_callable=AsyncMock)
    async def test_process_to_callback(self, devices_process):
        """Test process_telegram_incoming with callback."""

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
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        async_telegram_received_callback.assert_called_once_with(telegram)
        devices_process.assert_called_once_with(telegram)

    async def test_outgoing(self):
        """Test outgoing telegrams in telegram queue."""
        xknx = XKNX()

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        # log a warning if there is no KNXIP interface instantiated
        with pytest.raises(CommunicationError):
            await xknx.telegram_queue.process_telegram_outgoing(telegram)

        # if we have an interface send the telegram (doesn't raise)
        xknx.cemi_handler.send_telegram = AsyncMock()
        await xknx.telegram_queue.process_telegram_outgoing(telegram)
        xknx.cemi_handler.send_telegram.assert_called_once_with(telegram)

    @patch("logging.Logger.error")
    @patch("xknx.core.TelegramQueue.process_telegram_incoming", new_callable=MagicMock)
    async def test_process_exception(self, process_tg_in_mock, logging_error_mock):
        """Test process_telegram exception handling."""

        xknx = XKNX()

        async def process_exception():
            raise CouldNotParseTelegram(
                "Something went wrong when receiving the telegram."
            )

        process_tg_in_mock.return_value = asyncio.ensure_future(process_exception())

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        xknx.telegrams.put_nowait(telegram)
        await xknx.telegram_queue._process_all_telegrams()

        logging_error_mock.assert_called_once_with(
            "Error while processing telegram %s",
            CouldNotParseTelegram("Something went wrong when receiving the telegram."),
        )

    @patch("xknx.core.TelegramQueue.process_telegram_outgoing", new_callable=AsyncMock)
    @patch("xknx.core.TelegramQueue.process_telegram_incoming", new_callable=AsyncMock)
    async def test_process_all_telegrams(
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
        res = await xknx.telegram_queue._process_all_telegrams()

        assert res is None
        process_telegram_incoming_mock.assert_called_once()
        process_telegram_outgoing_mock.assert_called_once()

    #
    # TEST NO FILTERS
    #
    async def test_callback_no_filters(self):
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
        await xknx.telegram_queue._process_all_telegrams()

        async_telegram_received_callback.assert_called_with(telegram)

    #
    # TEST POSITIVE FILTERS
    #
    async def test_callback_positive_address_filters(self):
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
        await xknx.telegram_queue._process_all_telegrams()

        async_telegram_received_callback.assert_called_with(telegram)

    #
    # TEST NEGATIVE FILTERS
    #
    async def test_callback_negative_address_filters(self):
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
        await xknx.telegram_queue._process_all_telegrams()

        async_telegram_received_callback.assert_not_called()

    async def test_callback_group_addresses(self):
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
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        async_telegram_received_cb_one.assert_called_once_with(telegram)
        async_telegram_received_cb_two.assert_not_called()

        async_telegram_received_cb_one.reset_mock()
        # modify the filters - add/remove a GroupAddress
        callback_one.group_addresses.remove(GroupAddress("1/2/3"))
        callback_two.group_addresses.append(GroupAddress("1/2/3"))
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        async_telegram_received_cb_one.assert_not_called()
        async_telegram_received_cb_two.assert_called_once_with(telegram)

    #
    # TEST EXCEPTION HANDLING
    #
    @patch("logging.Logger.exception")
    @patch("xknx.xknx.Devices.process", side_effect=Exception)
    async def test_process_raising(self, process_mock, logging_exception_mock):
        """Test unexpected exception handling in telegram queues."""
        xknx = XKNX()
        telegram_in = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        # InternalGroupAddress to avoid CommunicationError for missing knxip_interface
        telegram_out = Telegram(
            destination_address=InternalGroupAddress("i-outgoing"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(0)),
        )
        xknx.telegrams.put_nowait(telegram_in)
        xknx.telegrams.put_nowait(telegram_out)

        await xknx.telegram_queue.start()
        await xknx.telegram_queue.stop()

        log_calls = [
            call(
                "Unexpected error while processing incoming telegram %s",
                telegram_in,
            ),
            call(
                "Unexpected error while processing outgoing telegram %s",
                telegram_out,
            ),
        ]
        logging_exception_mock.assert_has_calls(log_calls)

    @patch("logging.Logger.exception")
    async def test_callback_raising(self, logging_exception_mock):
        """Test telegram_received_callback raising an exception."""
        xknx = XKNX()
        good_callback_1 = AsyncMock()
        bad_callback = AsyncMock(side_effect=Exception("Boom"))
        good_callback_2 = AsyncMock()

        xknx.telegram_queue.register_telegram_received_cb(good_callback_1)
        xknx.telegram_queue.register_telegram_received_cb(bad_callback)
        xknx.telegram_queue.register_telegram_received_cb(good_callback_2)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)

        good_callback_1.assert_called_once_with(telegram)
        bad_callback.assert_called_once_with(telegram)
        good_callback_2.assert_called_once_with(telegram)

        logging_exception_mock.assert_called_once_with(
            "Unexpected error while processing telegram_received_cb for %s",
            telegram,
        )
