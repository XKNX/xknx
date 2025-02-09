"""Unit test for DateTime object."""

import datetime as dt
from unittest.mock import AsyncMock, patch

from freezegun import freeze_time
import pytest

from xknx import XKNX
from xknx.devices.datetime import (
    BROADCAST_MINUTES,
    DateDevice,
    DateTimeDevice,
    TimeDevice,
)
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from ..conftest import EventLoopClockAdvancer


class TestDateTime:
    """Test class for Time object."""

    @pytest.mark.parametrize(
        ("test_cls", "dt_value", "raw"),
        [
            (TimeDevice, dt.time(9, 13, 14), (0x9, 0xD, 0xE)),
            (DateDevice, dt.date(2017, 1, 7), (0x07, 0x01, 0x11)),
            (
                DateTimeDevice,
                dt.datetime(2017, 1, 7, 9, 13, 14),
                (0x75, 0x01, 0x07, 0x09, 0x0D, 0x0E, 0x24, 0x00),
            ),
        ],
    )
    async def test_process_set_custom_time(
        self,
        test_cls: type[DateDevice | DateTimeDevice | TimeDevice],
        dt_value: dt.time | dt.date | dt.datetime,
        raw: tuple[int],
    ) -> None:
        """Test setting a new time."""
        xknx = XKNX()
        test_device = test_cls(
            xknx,
            "Test",
            group_address="1/2/3",
            localtime=False,
        )
        assert test_device.value is None

        await test_device.set(dt_value)
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(raw)),
        )
        test_device.process(telegram)
        assert test_device.value == dt_value

    @pytest.mark.parametrize(
        ("cls", "raw_length", "raw"),
        [
            (TimeDevice, 3, (0xC9, 0xD, 0xE)),
            (DateDevice, 3, (0x07, 0x01, 0x11)),
            (DateTimeDevice, 8, (0x75, 0x01, 0x07, 0xC9, 0x0D, 0x0E, 0x20, 0xC0)),
        ],
    )
    async def test_sync_localtime(
        self,
        cls: type[DateDevice | DateTimeDevice | TimeDevice],
        raw_length: int,
        raw: tuple[int],
    ) -> None:
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        test_device = cls(xknx, "Test", group_address="1/2/3")

        with freeze_time("2017-01-07 09:13:14"):
            await test_device.sync()

        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/3")
        assert len(telegram.payload.value.value) == raw_length
        assert telegram.payload.value.value == raw

    async def test_sync_time_custom(self) -> None:
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        test_device = TimeDevice(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            localtime=False,
        )
        assert test_device.has_group_address(GroupAddress("1/2/4"))
        await test_device.sync()

        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/4")
        assert isinstance(telegram.payload, GroupValueRead)

    async def test_process_read_localtime(self) -> None:
        """Test test process a read telegram from KNX bus."""
        xknx = XKNX()
        test_device = TimeDevice(xknx, "TestDateTime", group_address="1/2/3")

        telegram_read = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        with freeze_time("2017-01-07 09:13:14"):
            test_device.process(telegram_read)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0xC9, 0xD, 0xE))),
        )

    async def test_process_read_custom_time(self) -> None:
        """Test test process a read telegram from KNX bus."""
        xknx = XKNX()
        test_device = TimeDevice(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            localtime=False,
            respond_to_read=True,
        )

        await test_device.set(dt.time(9, 13, 14))
        telegram_set = xknx.telegrams.get_nowait()
        assert telegram_set == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x9, 0xD, 0xE))),
        )
        test_device.process(telegram_set)

        telegram_read = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        test_device.process(telegram_read)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0x9, 0xD, 0xE))),
        )

    #
    # TEST HAS GROUP ADDRESS
    #
    async def test_has_group_address_localtime(self) -> None:
        """Test if has_group_address function works."""
        xknx = XKNX()
        test_device = DateDevice(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            localtime=True,
        )
        assert test_device.has_group_address(GroupAddress("1/2/3"))
        # group_address_state ignored when using localtime
        assert not test_device.has_group_address(GroupAddress("1/2/4"))

    async def test_has_group_address_custom_time(self) -> None:
        """Test if has_group_address function works."""
        xknx = XKNX()
        test_device = DateDevice(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            localtime=False,
        )
        assert test_device.has_group_address(GroupAddress("1/2/3"))
        assert test_device.has_group_address(GroupAddress("1/2/4"))

    #
    # TEST BACKGROUND TASK
    #
    @patch("xknx.core.TelegramQueue.process_telegram_outgoing", new_callable=AsyncMock)
    async def test_background_task(
        self,
        process_telegram_outgoing_mock: AsyncMock,
        time_travel: EventLoopClockAdvancer,
        xknx_no_interface: XKNX,
    ) -> None:
        """Test if background task works."""
        xknx = xknx_no_interface
        test_device = TimeDevice(xknx, "TestDateTime", group_address="1/2/3")
        xknx.devices.async_add(test_device)
        async with xknx:
            # initial time telegram
            await time_travel(0)
            process_telegram_outgoing_mock.assert_called_once()
            process_telegram_outgoing_mock.reset_mock()
            # repeated time telegram
            await time_travel(BROADCAST_MINUTES * 60)
            process_telegram_outgoing_mock.assert_called_once()
            process_telegram_outgoing_mock.reset_mock()
            # remove device - no more telegrams
            xknx.devices.async_remove(test_device)
            await time_travel(BROADCAST_MINUTES * 60)
            process_telegram_outgoing_mock.assert_not_called()

    @patch("xknx.core.TelegramQueue.process_telegram_outgoing", new_callable=AsyncMock)
    async def test_no_background_task(
        self,
        process_telegram_outgoing_mock: AsyncMock,
        time_travel: EventLoopClockAdvancer,
        xknx_no_interface: XKNX,
    ) -> None:
        """Test if background task is not started when not using `localtime`."""
        xknx = xknx_no_interface
        test_device = TimeDevice(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            localtime=False,
        )
        xknx.devices.async_add(test_device)
        async with xknx:
            assert test_device._broadcast_task is None
            # no initial time telegram
            await time_travel(0)
            process_telegram_outgoing_mock.assert_not_called()
            # no repeated time telegram
            await time_travel(BROADCAST_MINUTES * 60)
            process_telegram_outgoing_mock.assert_not_called()
