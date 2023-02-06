"""Unit test for value reader."""
import asyncio
from unittest.mock import MagicMock, patch

import pytest

from xknx import XKNX
from xknx.core import ValueReader
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


class TestValueReader:
    """Test class for value reader."""

    async def test_value_reader_read_success(self):
        """Test value reader: successful read."""
        xknx = XKNX()
        test_group_address = GroupAddress("0/0/0")
        response_telegram = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueResponse(DPTBinary(1)),
        )

        value_reader = ValueReader(xknx, test_group_address)
        # receive the response
        await value_reader.telegram_received(response_telegram)
        # and yield the result
        successful_read = await value_reader.read()

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        assert xknx.telegrams.qsize() == 1
        # Callback was removed again
        assert not xknx.telegram_queue.telegram_received_cbs
        # Telegram was received
        assert value_reader.received_telegram == response_telegram
        # successful read() returns the telegram
        assert successful_read == response_telegram

    @patch("logging.Logger.warning")
    async def test_value_reader_read_timeout(self, logger_warning_mock):
        """Test value reader: read timeout."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/0"))
        value_reader.response_received_event.wait = MagicMock(
            side_effect=asyncio.TimeoutError()
        )

        timed_out_read = await value_reader.read()

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        assert xknx.telegrams.qsize() == 1
        # Warning was logged
        logger_warning_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time (%s secs) to GroupValueRead request for: %s",
            2.0,
            GroupAddress("0/0/0"),
        )
        # Callback was removed again
        assert not xknx.telegram_queue.telegram_received_cbs
        # No telegram was received
        assert value_reader.received_telegram is None
        # Unsuccessful read() returns None
        assert timed_out_read is None

    async def test_value_reader_read_cancelled(self):
        """Test value reader: read cancelled."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/0"))
        value_reader.response_received_event.wait = MagicMock(
            side_effect=asyncio.CancelledError()
        )
        with pytest.raises(asyncio.CancelledError):
            await value_reader.read()

        # GroupValueRead telegram is still in the queue because we are not actually processing it
        assert xknx.telegrams.qsize() == 1
        # Callback was removed again
        assert not xknx.telegram_queue.telegram_received_cbs
        # No telegram was received
        assert value_reader.received_telegram is None

    async def test_value_reader_send_group_read(self):
        """Test value reader: send_group_read."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/0"))

        await value_reader.send_group_read()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("0/0/0"), payload=GroupValueRead()
        )

    async def test_value_reader_telegram_received(self):
        """Test value reader: telegram_received."""
        xknx = XKNX()
        test_group_address = GroupAddress("0/0/0")
        expected_telegram_1 = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueResponse(DPTBinary(1)),
        )
        expected_telegram_2 = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram_wrong_address = Telegram(
            destination_address=GroupAddress("0/0/1"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueResponse(DPTBinary(1)),
        )
        telegram_wrong_type = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueRead(),
        )

        value_reader = ValueReader(xknx, test_group_address)

        await value_reader.telegram_received(telegram_wrong_address)
        assert value_reader.received_telegram is None
        assert not value_reader.response_received_event.is_set()

        await value_reader.telegram_received(telegram_wrong_type)
        assert value_reader.received_telegram is None
        assert not value_reader.response_received_event.is_set()

        await value_reader.telegram_received(expected_telegram_1)
        assert value_reader.received_telegram == expected_telegram_1
        assert value_reader.response_received_event.is_set()

        await value_reader.telegram_received(expected_telegram_2)
        assert value_reader.received_telegram == expected_telegram_2
        assert value_reader.response_received_event.is_set()
