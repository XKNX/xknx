"""Unit test for DateTime object."""
import asyncio
import unittest

from xknx import XKNX
from xknx.devices import DateTime
from xknx.devices.datetime import DateTimeBroadcastType
from xknx.knx import GroupAddress, TelegramType


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
        self.loop.run_until_complete(asyncio.Task(datetime.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, GroupAddress('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 8)

    #
    # SYNC Date
    #
    def test_sync_date(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3', broadcast_type=DateTimeBroadcastType.DATE)
        self.loop.run_until_complete(asyncio.Task(datetime.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, GroupAddress('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 3)

    #
    # SYNC Time
    #
    def test_sync_time(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3', broadcast_type=DateTimeBroadcastType.TIME)
        self.loop.run_until_complete(asyncio.Task(datetime.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, GroupAddress('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 3)

    #
    # TEST HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test if has_group_address function works."""
        xknx = XKNX(loop=self.loop)
        datetime = DateTime(xknx, "TestDateTime", group_address='1/2/3')
        self.assertTrue(datetime.has_group_address(GroupAddress('1/2/3')))
        self.assertFalse(datetime.has_group_address(GroupAddress('1/2/4')))
