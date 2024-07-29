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


class TestDateTime:
    """Test class for Time object."""

    async def test_process_set_custom_time(self):
        """Test setting a new time."""
        xknx = XKNX()
        test_device = TimeDevice(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            localtime=False,
        )
        assert test_device.value is None

        test_time = dt.time(9, 13, 14)
        await test_device.set(test_time)
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x9, 0xD, 0xE))),
        )
        test_device.process(telegram)
        assert test_device.value == test_time

    @pytest.mark.parametrize(
        ("cls", "raw_length", "raw"),
        [
            (TimeDevice, 3, (0xC9, 0xD, 0xE)),
            (DateDevice, 3, (0x07, 0x01, 0x11)),
            (DateTimeDevice, 8, (0x75, 0x01, 0x07, 0xC9, 0x0D, 0x0E, 0x20, 0xC0)),
        ],
    )
    async def test_sync_localtime(self, cls, raw_length, raw):
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

    async def test_sync_time_custom(self):
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

    async def test_process_read_localtime(self):
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

    async def test_process_read_custom_time(self):
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
    async def test_has_group_address_localtime(self):
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

    async def test_has_group_address_custom_time(self):
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
        process_telegram_outgoing_mock,
        time_travel,
        xknx_no_interface,
    ):
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
        process_telegram_outgoing_mock,
        time_travel,
        xknx_no_interface,
    ):
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
