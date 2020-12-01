"""Unit test for DateTime object."""
import asyncio
import time
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.devices import DateTime
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


class TestDateTime(unittest.TestCase):
    """Test class for DateTime object."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SYNC DateTime
    #
    def test_sync_datetime(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="DATETIME"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(datetime.sync())

        # initial Telegram from broadcasting on init
        self.assertEqual(xknx.telegrams.qsize(), 2)
        _throwaway_initial = xknx.telegrams.get_nowait()

        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.destination_address, GroupAddress("1/2/3"))
        self.assertEqual(len(telegram.payload.dpt.value), 8)
        self.assertEqual(
            telegram.payload.dpt.value, (0x75, 0x01, 0x07, 0xE9, 0x0D, 0x0E, 0x20, 0x80)
        )

    #
    # SYNC Date
    #
    def test_sync_date(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="DATE"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(datetime.sync())

        # initial Telegram from broadcasting on init
        self.assertEqual(xknx.telegrams.qsize(), 2)
        _throwaway_initial = xknx.telegrams.get_nowait()

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.destination_address, GroupAddress("1/2/3"))
        self.assertEqual(len(telegram.payload.dpt.value), 3)
        self.assertEqual(telegram.payload.dpt.value, (0x07, 0x01, 0x11))

    #
    # SYNC Time
    #
    def test_sync_time(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", broadcast_type="TIME"
        )

        with patch("time.localtime") as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(datetime.sync())

        # initial Telegram from broadcasting on init
        self.assertEqual(xknx.telegrams.qsize(), 2)
        _throwaway_initial = xknx.telegrams.get_nowait()

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.destination_address, GroupAddress("1/2/3"))
        self.assertEqual(len(telegram.payload.dpt.value), 3)
        self.assertEqual(telegram.payload.dpt.value, (0xE9, 0x0D, 0x0E))

    #
    # PROCESS
    #
    #
    # TEST PROCESS
    #
    def test_process_read(self):
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
            self.loop.run_until_complete(datetime.process(telegram_read))

        # initial Telegram from broadcasting on init
        self.assertEqual(xknx.telegrams.qsize(), 2)
        _throwaway_initial = xknx.telegrams.get_nowait()

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueResponse(DPTArray((0xE9, 0xD, 0xE))),
            ),
        )

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test if has_group_address function works."""
        xknx = XKNX()
        datetime = DateTime(
            xknx, "TestDateTime", group_address="1/2/3", localtime=False
        )
        self.assertTrue(datetime.has_group_address(GroupAddress("1/2/3")))
        self.assertFalse(datetime.has_group_address(GroupAddress("1/2/4")))
