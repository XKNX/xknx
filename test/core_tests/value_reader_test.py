"""Unit test for value reader."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xknx import XKNX
from xknx.core import ValueReader
from xknx.core.value_reader import MAX_SEND_WAIT_TIME
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from ..conftest import EventLoopClockAdvancer


class TestValueReader:
    """Test class for value reader."""

    async def test_value_reader_read_success(self) -> None:
        """Test value reader: successful read."""
        xknx = XKNX()
        test_group_address = GroupAddress("0/0/1")
        response_telegram = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueResponse(DPTBinary(1)),
        )

        value_reader = ValueReader(xknx, test_group_address)
        # receive the response
        value_reader.telegram_received(response_telegram)
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
    @patch("xknx.cemi.CEMIHandler.send_telegram", new_callable=AsyncMock)
    async def test_value_reader_read_timeout(
        self,
        _send_telegram_mock: AsyncMock,
        logger_warning_mock: MagicMock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test value reader: read timeout starts when the GroupValueRead was sent."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/1"))

        read_task = asyncio.create_task(value_reader.read())
        await asyncio.sleep(0)
        assert xknx.telegrams.qsize() == 1
        # the GroupValueRead waits in the queue - the response timeout is not running
        await time_travel(value_reader.timeout_in_seconds)
        assert not read_task.done()
        assert not value_reader.sent
        # send it
        await xknx.telegram_queue._process_all_telegrams()
        assert value_reader.sent
        assert not read_task.done()
        logger_warning_mock.assert_not_called()
        await time_travel(value_reader.timeout_in_seconds)
        assert read_task.done()
        # Warning was logged
        logger_warning_mock.assert_called_once_with(
            "Error: KNX bus did not respond in time (%s secs) to GroupValueRead request for: %s",
            2.0,
            GroupAddress("0/0/1"),
        )
        # Callback was removed again
        assert not xknx.telegram_queue.telegram_received_cbs
        # No telegram was received
        assert value_reader.received_telegram is None
        # Unsuccessful read() returns None
        assert read_task.result() is None

    @patch("logging.Logger.warning")
    @patch("xknx.cemi.CEMIHandler.send_telegram", new_callable=AsyncMock)
    async def test_value_reader_read_response_after_queue(
        self,
        _send_telegram_mock: AsyncMock,
        logger_warning_mock: MagicMock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test value reader: a response in time after a delayed send is successful."""
        xknx = XKNX()
        test_group_address = GroupAddress("0/0/1")
        response_telegram = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueResponse(DPTBinary(1)),
        )
        value_reader = ValueReader(xknx, test_group_address)

        read_task = asyncio.create_task(value_reader.read())
        await asyncio.sleep(0)
        # outgoing queue is busy for longer than the response timeout
        await time_travel(value_reader.timeout_in_seconds * 2)
        await xknx.telegram_queue._process_all_telegrams()
        assert value_reader.sent
        await time_travel(value_reader.timeout_in_seconds / 2)
        assert not read_task.done()
        value_reader.telegram_received(response_telegram)
        await asyncio.sleep(0)
        assert read_task.done()
        assert read_task.result() == response_telegram
        logger_warning_mock.assert_not_called()
        assert not xknx.telegram_queue.telegram_received_cbs

    @patch("logging.Logger.warning")
    async def test_value_reader_read_not_sent(
        self,
        logger_warning_mock: MagicMock,
        time_travel: EventLoopClockAdvancer,
    ) -> None:
        """Test value reader: give up when the GroupValueRead can't be sent."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/1"))

        read_task = asyncio.create_task(value_reader.read())
        await asyncio.sleep(0)
        await time_travel(MAX_SEND_WAIT_TIME)
        assert read_task.done()
        assert read_task.result() is None
        assert not value_reader.sent
        # GroupValueRead telegram is still in the queue because we are not actually processing it
        assert xknx.telegrams.qsize() == 1
        logger_warning_mock.assert_called_once_with(
            "Error: GroupValueRead request for %s could not be sent in time (%s secs)",
            GroupAddress("0/0/1"),
            MAX_SEND_WAIT_TIME,
        )
        assert not xknx.telegram_queue.telegram_received_cbs

    async def test_value_reader_read_cancelled(self) -> None:
        """Test value reader: read cancelled."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/1"))
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

    async def test_value_reader_send_group_read(self) -> None:
        """Test value reader: send_group_read."""
        xknx = XKNX()
        value_reader = ValueReader(xknx, GroupAddress("0/0/1"))

        value_reader.send_group_read()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("0/0/1"), payload=GroupValueRead()
        )

    async def test_value_reader_telegram_received(self) -> None:
        """Test value reader: telegram_received."""
        xknx = XKNX()
        test_group_address = GroupAddress("0/0/1")
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
            destination_address=GroupAddress("0/0/2"),
            direction=TelegramDirection.INCOMING,
            payload=GroupValueResponse(DPTBinary(1)),
        )
        telegram_wrong_type = Telegram(
            destination_address=test_group_address,
            direction=TelegramDirection.INCOMING,
            payload=GroupValueRead(),
        )

        value_reader = ValueReader(xknx, test_group_address)

        value_reader.telegram_received(telegram_wrong_address)
        assert value_reader.received_telegram is None
        assert not value_reader.response_received_event.is_set()

        value_reader.telegram_received(telegram_wrong_type)
        assert value_reader.received_telegram is None
        assert not value_reader.response_received_event.is_set()
        assert not value_reader.sent

        # our own GroupValueRead passing the outgoing queue
        value_reader.telegram_received(
            Telegram(destination_address=test_group_address, payload=GroupValueRead())
        )
        assert value_reader.received_telegram is None
        assert not value_reader.response_received_event.is_set()
        assert value_reader.sent

        value_reader.telegram_received(expected_telegram_1)
        assert value_reader.received_telegram == expected_telegram_1
        assert value_reader.response_received_event.is_set()

        value_reader.telegram_received(expected_telegram_2)
        assert value_reader.received_telegram == expected_telegram_2
        assert value_reader.response_received_event.is_set()
