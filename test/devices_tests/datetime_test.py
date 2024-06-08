"""Unit test for DateTime object."""

import time
from unittest.mock import AsyncMock, patch

from xknx import XKNX
from xknx.devices.datetime import BROADCAST_MINUTES, DateTime
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


class TestDateTime:
    """Test class for DateTime object."""

    #
    # SET Time
    #
    async def test_process_set_custom_time(self):
        """Test setting a new time."""
        xknx = XKNX()
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            broadcast_type="TIME",
            localtime=False,
        )
        assert datetime.remote_value.value is None

        test_time = time.strptime("9:13:14", "%H:%M:%S")
        await datetime.set(test_time)
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x9, 0xD, 0xE))),
        )
        await datetime.process(telegram)
        assert datetime.remote_value.value == test_time

    #
    # SYNC DateTime
    #
    async def test_sync_datetime(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="DATETIME"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await datetime.sync()

        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/3")
        assert len(telegram.payload.value.value) == 8
        assert telegram.payload.value.value == (
            0x75,
            0x01,
            0x07,
            0xE9,
            0x0D,
            0x0E,
            0x20,
            0x80,
        )

    #
    # SYNC Date
    #
    async def test_sync_date(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="DATE"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await datetime.sync()

        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/3")
        assert len(telegram.payload.value.value) == 3
        assert telegram.payload.value.value == (0x07, 0x01, 0x11)

    #
    # SYNC Time
    #
    async def test_sync_time_local(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            broadcast_type="TIME",
        )
        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await datetime.sync()

        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/3")
        assert len(telegram.payload.value.value) == 3
        assert telegram.payload.value.value == (0xE9, 0x0D, 0x0E)

    async def test_sync_time_custom(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            broadcast_type="TIME",
            localtime=False,
        )
        assert datetime.has_group_address(GroupAddress("1/2/4"))
        await datetime.sync()

        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/4")
        assert isinstance(telegram.payload, GroupValueRead)

    #
    # PROCESS
    #
    #
    # TEST PROCESS
    #
    async def test_process_read_localtime(self):
        """Test test process a read telegram from KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="TIME"
        )

        telegram_read = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await datetime.process(telegram_read)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0xE9, 0xD, 0xE))),
        )

    async def test_process_read_custom_time(self):
        """Test test process a read telegram from KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            broadcast_type="TIME",
            localtime=False,
            respond_to_read=True,
        )

        datetime.remote_value.value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
        telegram_read = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        await datetime.process(telegram_read)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0xE9, 0xD, 0xE))),
        )

    #
    # TEST HAS GROUP ADDRESS
    #
    async def test_has_group_address_localtime(self):
        """Test if has_group_address function works."""
        xknx = XKNX()
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            localtime=True,
        )
        assert datetime.has_group_address(GroupAddress("1/2/3"))
        # group_address_state ignored when using localtime
        assert not datetime.has_group_address(GroupAddress("1/2/4"))

    async def test_has_group_address_custom_time(self):
        """Test if has_group_address function works."""
        xknx = XKNX()
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            localtime=False,
        )
        assert datetime.has_group_address(GroupAddress("1/2/3"))
        assert datetime.has_group_address(GroupAddress("1/2/4"))

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
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="TIME"
        )
        xknx.devices.async_add(datetime)
        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
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
                xknx.devices.async_remove(datetime)
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
        datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            broadcast_type="TIME",
            localtime=False,
        )
        xknx.devices.async_add(datetime)
        async with xknx:
            assert datetime._broadcast_task is None
            # no initial time telegram
            await time_travel(0)
            process_telegram_outgoing_mock.assert_not_called()
            # no repeated time telegram
            await time_travel(BROADCAST_MINUTES * 60)
            process_telegram_outgoing_mock.assert_not_called()
