import unittest
from unittest.mock import Mock
import asyncio
from xknx import XKNX, Shutter
from xknx.knx import Telegram, Address, TelegramType, DPTBinary, DPTArray

class TestShutter(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    #
    # SYNC
    #
    def test_sync(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        self.loop.run_until_complete(asyncio.Task(shutter.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(Address('1/2/4'), TelegramType.GROUP_READ))


    #
    # TEST SET UP
    #
    def test_set_up(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        shutter.set_up()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/1'), payload=DPTBinary(0)))


    #
    # TEST SET DOWN
    #
    def test_set_short_down(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        shutter.set_down()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/1'), payload=DPTBinary(1)))


    #
    # TEST SET SHORT UP
    #
    def test_set_short_up(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        shutter.set_short_up()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/2'), payload=DPTBinary(0)))


    #
    # TEST SET SHORT DOWN
    #
    def test_set_down(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        shutter.set_short_down()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/2'), payload=DPTBinary(1)))


    #
    # TEST STOP
    #
    def test_stop(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx, 'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        shutter.stop()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/2'), payload=DPTBinary(1)))


    #
    # TEST POSITION
    #
    def test_position(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')
        shutter.set_position(50)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/3'), payload=DPTArray(50)))


    def test_position_without_position_address_up(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position_feedback='1/2/4')
        shutter.travelcalculator.set_position(40)
        shutter.set_position(50)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/1'), payload=DPTBinary(1)))


    def test_position_without_position_address_down(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position_feedback='1/2/4')
        shutter.travelcalculator.set_position(100)
        shutter.set_position(50)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(Address('1/2/1'), payload=DPTBinary(0)))


    #
    # TEST PROCESS
    #
    def test_process(self):
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')

        telegram = Telegram(Address('1/2/4'), payload=DPTArray(42))
        shutter.process(telegram)

        self.assertEqual(shutter.current_position(), 42)


    def test_process_callback(self):
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop, start=False)
        shutter = Shutter(
            xknx,
            'TestShutter',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_feedback='1/2/4')

        after_update_callback = Mock()
        shutter.register_device_updated_cb(after_update_callback)

        telegram = Telegram(Address('1/2/4'), payload=DPTArray(42))
        shutter.process(telegram)

        after_update_callback.assert_called_with(shutter)


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestShutter)
unittest.TextTestRunner(verbosity=2).run(SUITE)
