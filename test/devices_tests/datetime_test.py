"""Unit test for DateTime object."""
import time
from unittest.mock import patch

from xknx import XKNX
from xknx.devices import DateTime
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse


class TestDateTime:
    """Test class for DateTime object."""

    # pylint: disable=attribute-defined-outside-init
    def teardown_method(self):
        """Cancel broadcast_task."""
        self.datetime.__del__()

    #
    # SYNC DateTime
    #
    async def test_sync_datetime(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        self.datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="DATETIME"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await self.datetime.sync()

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
        self.datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="DATE"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await self.datetime.sync()

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
        self.datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            broadcast_type="TIME",
        )
        # group_address_state ignored when using localtime
        assert not self.datetime.has_group_address("1/2/4")

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await self.datetime.sync()

        telegram = xknx.telegrams.get_nowait()
        assert telegram.destination_address == GroupAddress("1/2/3")
        assert len(telegram.payload.value.value) == 3
        assert telegram.payload.value.value == (0xE9, 0x0D, 0x0E)

    async def test_sync_time_custom(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        self.datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            group_address_state="1/2/4",
            broadcast_type="TIME",
            localtime=False,
        )
        assert self.datetime.has_group_address(GroupAddress("1/2/4"))
        await self.datetime.sync()

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
        self.datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="TIME"
        )

        telegram_read = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            await self.datetime.process(telegram_read)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0xE9, 0xD, 0xE))),
        )

    async def test_process_read_custom_time(self):
        """Test test process a read telegram from KNX bus."""
        xknx = XKNX()
        self.datetime = DateTime(
            xknx,
            "TestDateTime",
            group_address="1/2/3",
            broadcast_type="TIME",
            localtime=False,
            respond_to_read=True,
        )

        self.datetime.remote_value.value = time.struct_time(
            [2017, 1, 7, 9, 13, 14, 6, 0, 0]
        )
        telegram_read = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )
        await self.datetime.process(telegram_read)

        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTArray((0xE9, 0xD, 0xE))),
        )

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test if has_group_address function works."""
        xknx = XKNX()
        self.datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", localtime=False
        )
        assert self.datetime.has_group_address(GroupAddress("1/2/3"))
        assert not self.datetime.has_group_address(GroupAddress("1/2/4"))
