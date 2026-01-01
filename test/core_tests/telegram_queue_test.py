"""Unit test for telegram received callback."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CommunicationError, CouldNotParseTelegram
from xknx.telegram import AddressFilter, Telegram, TelegramDirection
from xknx.telegram.address import GroupAddress, IndividualAddress, InternalGroupAddress
from xknx.telegram.apci import GroupValueWrite


class TestTelegramQueue:
    """Test class for telegram queue."""

    #
    # TEST START, RUN, STOP
    #
    async def test_start(self) -> None:
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
    async def test_rate_limit(self, async_sleep_mock: AsyncMock) -> None:
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
    async def test_register(self) -> None:
        """Test telegram_received_callback after state of switch was changed."""

        xknx = XKNX()
        telegram_received_cb = Mock()
        xknx.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        telegram_received_cb.assert_called_once_with(telegram)

    async def test_register_with_outgoing_telegrams(self) -> None:
        """Test telegram_received_callback with outgoing telegrams."""

        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()
        telegram_received_cb = Mock()
        xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_cb, None, None, True
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await xknx.telegram_queue.process_telegram_outgoing(telegram)
        telegram_received_cb.assert_called_once_with(telegram)

    async def test_register_with_outgoing_telegrams_does_not_trigger(self) -> None:
        """Test telegram_received_callback with outgoing telegrams."""

        xknx = XKNX()
        xknx.cemi_handler = AsyncMock()
        telegram_received_cb = Mock()
        xknx.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await xknx.telegram_queue.process_telegram_outgoing(telegram)
        telegram_received_cb.assert_not_called()

    #
    # TEST UNREGISTER
    #
    async def test_unregister(self) -> None:
        """Test telegram_received_callback after state of switch was changed."""

        xknx = XKNX()
        telegram_received_cb = Mock()

        callback = xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_cb
        )
        xknx.telegram_queue.unregister_telegram_received_cb(callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        telegram_received_cb.assert_not_called()

    #
    # TEST PROCESS
    #
    @patch("xknx.devices.Devices.devices_by_group_address")
    async def test_process_to_device(self, devices_by_ga_mock: Mock) -> None:
        """Test process_telegram_incoming for forwarding telegram to a device."""

        xknx = XKNX()
        test_device = Mock()
        devices_by_ga_mock.return_value = [test_device]

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        devices_by_ga_mock.assert_called_once_with(GroupAddress("1/2/3"))
        test_device.process.assert_called_once_with(telegram)

    @patch("xknx.devices.Devices.process")
    async def test_process_to_callback(self, devices_process: MagicMock) -> None:
        """Test process_telegram_incoming with callback."""
        xknx = XKNX()
        telegram_received_cb = Mock()

        xknx.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        telegram_received_cb.assert_called_once_with(telegram)
        devices_process.assert_called_once_with(telegram)

    async def test_callback_decoded_telegram_data(self) -> None:
        """Test telegram_received_callback having decoded telegram data."""

        xknx = XKNX()
        xknx.group_address_dpt.set({"1/2/3": {"main": 5, "sub": 1}})
        telegram_received_cb = Mock()
        xknx.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(
                DPTArray(
                    0x7F,
                )
            ),
        )
        await xknx.telegram_queue.start()
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegrams.join()
        await xknx.telegram_queue.stop()

        assert telegram_received_cb.call_count == 1
        received = telegram_received_cb.call_args_list[0][0][0]
        assert received == telegram
        assert received.decoded_data is not None
        assert received.decoded_data.value == 50

    async def test_outgoing(self) -> None:
        """Test outgoing telegrams in telegram queue."""
        xknx = XKNX()

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.OUTGOING,
            payload=GroupValueWrite(DPTBinary(1)),
        )

        # log a warning if there is no KNXIP interface instantiated
        with pytest.raises(CommunicationError):  # from xknx.knxip_interface.send_cemi
            await xknx.telegram_queue.process_telegram_outgoing(telegram)

    @patch("logging.Logger.error")
    @patch("xknx.core.TelegramQueue.process_telegram_incoming", new_callable=MagicMock)
    async def test_process_exception(
        self, process_tg_in_mock: MagicMock, logging_error_mock: MagicMock
    ) -> None:
        """Test process_telegram exception handling."""

        xknx = XKNX()

        async def process_exception() -> None:
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
        self,
        process_telegram_incoming_mock: AsyncMock,
        process_telegram_outgoing_mock: AsyncMock,
    ) -> None:
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
        await xknx.telegram_queue._process_all_telegrams()

        process_telegram_incoming_mock.assert_called_once()
        process_telegram_outgoing_mock.assert_called_once()

    #
    # TEST NO FILTERS
    #
    async def test_callback_no_filters(self) -> None:
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        telegram_received_cb = Mock()

        xknx.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegram_queue._process_all_telegrams()

        telegram_received_cb.assert_called_with(telegram)

    #
    # TEST POSITIVE FILTERS
    #
    async def test_callback_positive_address_filters(self) -> None:
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        telegram_received_cb = Mock()

        xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_cb,
            address_filters=[AddressFilter("2/4-8/*"), AddressFilter("1/2/-8")],
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegram_queue._process_all_telegrams()

        telegram_received_cb.assert_called_with(telegram)

    #
    # TEST NEGATIVE FILTERS
    #
    async def test_callback_negative_address_filters(self) -> None:
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        telegram_received_cb = Mock()

        xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_cb,
            address_filters=[AddressFilter("2/4-8/*"), AddressFilter("1/2/8-")],
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        xknx.telegrams.put_nowait(telegram)
        await xknx.telegram_queue._process_all_telegrams()

        telegram_received_cb.assert_not_called()

    async def test_callback_group_addresses(self) -> None:
        """Test telegram_received_callback after state of switch was changed."""
        xknx = XKNX()
        telegram_received_cb_one = Mock()
        telegram_received_cb_two = Mock()

        callback_one = xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_cb_one,
            address_filters=[],
            group_addresses=[GroupAddress("1/2/3")],
        )
        callback_two = xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_cb_two, address_filters=[], group_addresses=[]
        )

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        telegram_received_cb_one.assert_called_once_with(telegram)
        telegram_received_cb_two.assert_not_called()

        telegram_received_cb_one.reset_mock()
        # modify the filters - add/remove a GroupAddress
        callback_one.group_addresses.remove(GroupAddress("1/2/3"))
        callback_two.group_addresses.append(GroupAddress("1/2/3"))
        await xknx.telegram_queue.process_telegram_incoming(telegram)
        telegram_received_cb_one.assert_not_called()
        telegram_received_cb_two.assert_called_once_with(telegram)

    #
    # TEST EXCEPTION HANDLING
    #
    @patch("logging.Logger.exception")
    @patch("xknx.xknx.Devices.process", side_effect=Exception)
    async def test_process_raising(
        self, process_mock: MagicMock, logging_exception_mock: MagicMock
    ) -> None:
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
    async def test_callback_raising(self, logging_exception_mock: MagicMock) -> None:
        """Test telegram_received_callback raising an exception."""
        xknx = XKNX()
        good_callback_1 = Mock()
        bad_callback = Mock(side_effect=Exception("Boom"))
        good_callback_2 = Mock()

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

    @pytest.mark.parametrize(
        ("raw_cemi_data_secure", "should_callback_called"),
        [
            # src = 4.0.9; dst = 0/4/0; GroupValueResponse; value=(116, 41, 41)
            # A+C; seq_num=155806854986
            (
                bytes.fromhex("29003ce0400904001103f110002446cfef4ac085e7092ab062b44d"),
                True,  # for GroupValueResponse
            ),
            # Property Value Write PID_GRP_KEY_TABLE connectionless
            # Object Idx = 5, PropId = 35h, Element Count = 1, Index = 1
            # Data = 20 21 22 23 24 25 26 27 28 29 2A 2B 2C 2D 2E 2F
            # A+C
            # from AN158 v07 KNX Data Security AS - Annex A example
            (
                bytes.fromhex(
                    "29 00 b0 60 ff 67 ff 00 22 03 f1 90 00 00 00 00"
                    "00 04 67 67 24 2a 23 08 ca 76 a1 17 74 21 4e e4"
                    "cf 5d 94 90 9f 74 3d 05 0d 8f c1 68"
                ),
                False,  # for destination address is IndividualAddress
            ),
        ],
    )
    def test_data_secure_group_key_issue_callback(
        self, raw_cemi_data_secure: bytes, should_callback_called: bool
    ) -> None:
        """Test incoming undecodable DataSecure Telegram callback."""
        xknx = XKNX()
        xknx.current_address = IndividualAddress("5.0.1")

        data_secure_issue_cb = Mock()
        unsub = xknx.telegram_queue.register_data_secure_group_key_issue_cb(
            data_secure_issue_cb
        )

        xknx.cemi_handler.handle_raw_cemi(raw_cemi_data_secure)
        assert data_secure_issue_cb.called == should_callback_called
        data_secure_issue_cb.reset_mock()

        unsub()
        xknx.cemi_handler.handle_raw_cemi(raw_cemi_data_secure)
        data_secure_issue_cb.assert_not_called()
