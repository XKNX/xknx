"""Unit test for Time object."""
import unittest
import asyncio
from xknx import XKNX
from xknx.devices import Time
from xknx.knx import Address, TelegramType


class TestTime(unittest.TestCase):
    """Test class for Time object."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        time = Time(xknx, "TestTime", group_address='1/2/3')
        self.loop.run_until_complete(asyncio.Task(time.sync(False)))

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, Address('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 3)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTime)
unittest.TextTestRunner(verbosity=2).run(SUITE)
