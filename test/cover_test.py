"""Unit test for Cover objects."""

import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import Cover
from xknx.knx import GroupAddress, DPTArray, DPTBinary, Telegram, TelegramType


class TestCover(unittest.TestCase):
    """Test class for Cover objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # SUPPORTS_POSITION/ANGLE
    #
    def test_supports_position_true(self):
        """Test support_position_true."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'Children.Venetian',
            group_address_long='1/4/14',
            group_address_short='1/4/15',
            group_address_position='1/4/16')
        self.assertTrue(cover.supports_position)

    def test_supports_position_false(self):
        """Test support_position_true."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'Children.Venetian',
            group_address_long='1/4/14',
            group_address_short='1/4/15')
        self.assertFalse(cover.supports_position)

    def test_supports_angle_true(self):
        """Test support_position_true."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'Children.Venetian',
            group_address_long='1/4/14',
            group_address_short='1/4/15',
            group_address_angle='1/4/18')
        self.assertTrue(cover.supports_angle)

    def test_support_angle_false(self):
        """Test support_position_true."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'Children.Venetian',
            group_address_long='1/4/14',
            group_address_short='1/4/15')
        self.assertFalse(cover.supports_angle)

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3')
        self.loop.run_until_complete(asyncio.Task(cover.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))

    def test_sync_state(self):
        """Test sync function with explicit state address."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    def test_sync_angle(self):
        """Test sync function for cover with angle."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_angle='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/3'), TelegramType.GROUP_READ))
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram2,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    def test_sync_angle_state(self):
        """Test sync function with angle/explicit state."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_angle='1/2/3',
            group_address_angle_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.sync(False)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(telegram1,
                         Telegram(GroupAddress('1/2/4'), TelegramType.GROUP_READ))

    #
    # TEST SET UP
    #
    def test_set_up(self):
        """Test moving cover to 'up' position."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.set_up()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTBinary(0)))

    #
    # TEST SET DOWN
    #
    def test_set_short_down(self):
        """Test moving cover to 'down' position."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.set_down()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTBinary(1)))

    #
    # TEST SET SHORT UP
    #
    def test_set_short_up(self):
        """Test moving cover 'short up'."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.set_short_up()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/2'), payload=DPTBinary(1)))

    #
    # TEST SET SHORT DOWN
    #
    def test_set_down(self):
        """Test moving cover 'short down'."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.set_short_down()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/2'), payload=DPTBinary(0)))

    #
    # TEST STOP
    #
    def test_stop(self):
        """Test stopping cover."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx, 'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.stop()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/2'), payload=DPTBinary(0)))

    #
    # TEST POSITION
    #
    def test_position(self):
        """Test moving cover to absolute position."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        self.loop.run_until_complete(asyncio.Task(cover.set_position(50)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/3'), payload=DPTArray(0x80)))

    def test_position_without_position_address_up(self):
        """Test moving cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position_state='1/2/4')
        cover.travelcalculator.set_position(60)
        self.loop.run_until_complete(asyncio.Task(cover.set_position(50)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTBinary(1)))

    def test_position_without_position_address_down(self):
        """Test moving cover down - with no absolute positioning supported."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position_state='1/2/4')
        cover.travelcalculator.set_position(70)
        self.loop.run_until_complete(asyncio.Task(cover.set_position(80)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/2/1'), payload=DPTBinary(0)))

    def test_angle(self):
        """Test changing angle."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'Children.Venetian',
            group_address_long='1/4/14',
            group_address_short='1/4/15',
            group_address_position_state='1/4/17',
            group_address_position='1/4/16',
            group_address_angle='1/4/18',
            group_address_angle_state='1/4/19')
        self.loop.run_until_complete(asyncio.Task(cover.set_angle(50)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(telegram,
                         Telegram(GroupAddress('1/4/18'), payload=DPTArray(0x80)))

    #
    # TEST PROCESS
    #
    def test_process(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')
        telegram = Telegram(GroupAddress('1/2/4'), payload=DPTArray(42))
        self.loop.run_until_complete(asyncio.Task(cover.process(telegram)))
        self.assertEqual(cover.current_position(), 84)

    def test_process_angle(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_angle='1/2/3',
            group_address_angle_state='1/2/4')
        telegram = Telegram(GroupAddress('1/2/4'), payload=DPTArray(42))
        self.loop.run_until_complete(asyncio.Task(cover.process(telegram)))
        self.assertEqual(cover.angle.value, 84)

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed."""
        # pylint: disable=no-self-use
        xknx = XKNX(loop=self.loop)
        cover = Cover(
            xknx,
            'TestCover',
            group_address_long='1/2/1',
            group_address_short='1/2/2',
            group_address_position='1/2/3',
            group_address_position_state='1/2/4')

        after_update_callback = Mock()

        @asyncio.coroutine
        def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)
        cover.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(GroupAddress('1/2/4'), payload=DPTArray(42))
        self.loop.run_until_complete(asyncio.Task(cover.process(telegram)))

        after_update_callback.assert_called_with(cover)
