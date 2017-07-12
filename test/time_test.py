import unittest
import asyncio

from xknx import XKNX, Time
from xknx.knx import Address, TelegramType

class TestTime(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # SYNC STATE
    #
    def test_sync_state(self):

        xknx = XKNX(loop=self.loop, start=False)
        time = Time(xknx, "TestTime", group_address='1/2/3')
        time.sync_state()

        self.assertEqual(xknx.telegrams.qsize(), 1)

        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram.group_address, Address('1/2/3'))
        self.assertEqual(telegram.telegramtype, TelegramType.GROUP_WRITE)
        self.assertEqual(len(telegram.payload.value), 3)

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTime)
unittest.TextTestRunner(verbosity=2).run(SUITE)
