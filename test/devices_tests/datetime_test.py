"""Unit test for DateTime object."""
import asyncio
import time
import unittest
from unittest.mock import patch

from xknx import XKNX
from xknx.devices import DateTime, DateTimeBroadcastType
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram, TelegramType


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
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3', broadcast_type=DateTimeBroadcastType.DATETIME)

        with patch('time.localtime') as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(asyncio.Task(datetime.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, GroupAddress('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 8)
        self.assertEqual(telegram.payload.value, (0x75, 0x01, 0x07, 0xE9, 0x0D, 0x0E, 0x0, 0x0))

    #
    # SYNC Date
    #
    def test_sync_date(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3', broadcast_type=DateTimeBroadcastType.DATE)
        with patch('time.localtime') as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(asyncio.Task(datetime.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, GroupAddress('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 3)
        self.assertEqual(telegram.payload.value, (0x07, 0x01, 0x11))

    #
    # SYNC Time
    #
    def test_sync_time(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3', broadcast_type=DateTimeBroadcastType.TIME)
        with patch('time.localtime') as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(asyncio.Task(datetime.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, GroupAddress('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 3)
        self.assertEqual(telegram.payload.value, (0xE9, 0x0D, 0x0E))

    #
    # PROCESS
    #
    #
    # TEST PROCESS
    #
    def test_process_read(self):
        """Test test process a read telegram from KNX bus."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3', broadcast_type=DateTimeBroadcastType.TIME)

        telegram_read = Telegram(
            group_address=GroupAddress('1/2/3'),
            telegramtype=TelegramType.GROUP_READ)
        with patch('time.localtime') as mock_time:
            mock_time.return_value = time.struct_time([2017, 1, 7, 9, 13, 14, 6, 0, 0])
            self.loop.run_until_complete(asyncio.Task(datetime.process(telegram_read)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                group_address=GroupAddress('1/2/3'),
                telegramtype=TelegramType.GROUP_RESPONSE,
                payload=DPTArray((0xe9, 0xd, 0xe))))

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test if has_group_address function works."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3')
        self.assertTrue(datetime.has_group_address(GroupAddress('1/2/3')))
        self.assertFalse(datetime.has_group_address(GroupAddress('1/2/4')))
