"""Unit test for Cover objects."""

import asyncio
import unittest
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.devices import Cover
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


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
    # SUPPORTS STOP/POSITION/ANGLE
    #
    def test_supports_stop_true(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover_short_stop = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        self.assertTrue(cover_short_stop.supports_stop)

        cover_manual_stop = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_stop="1/4/15",
        )
        self.assertTrue(cover_manual_stop.supports_stop)

    def test_supports_stop_false(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_position="1/4/16",
            group_address_angle="1/4/18",
        )
        self.assertFalse(cover.supports_stop)
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(cover.stop())
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Stop not supported for device %s", "Children.Venetian"
            )

    def test_supports_position_true(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_position="1/4/16",
        )
        self.assertTrue(cover.supports_position)

    def test_supports_position_false(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        self.assertFalse(cover.supports_position)

    def test_supports_angle_true(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_angle="1/4/18",
        )
        self.assertTrue(cover.supports_angle)

    def test_support_angle_false(self):
        """Test support_position_true."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        self.assertFalse(cover.supports_angle)

    #
    # SYNC
    #
    def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/3",
        )
        self.loop.run_until_complete(cover.sync())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
            ),
        )

    def test_sync_state(self):
        """Test sync function with explicit state address."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover.sync())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
            ),
        )

    def test_sync_angle(self):
        """Test sync function for cover with angle."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/3",
            group_address_angle_state="1/2/4",
        )
        self.loop.run_until_complete(cover.sync())
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
            ),
        )
        telegram2 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram2,
            Telegram(
                destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
            ),
        )

    def test_sync_angle_state(self):
        """Test sync function with angle/explicit state."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_angle="1/2/3",
            group_address_angle_state="1/2/4",
        )
        self.loop.run_until_complete(cover.sync())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram1 = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram1,
            Telegram(
                destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
            ),
        )

    #
    # TEST SET UP
    #
    def test_set_up(self):
        """Test moving cover to 'up' position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover.set_up())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )

    #
    # TEST SET DOWN
    #
    def test_set_short_down(self):
        """Test moving cover to 'down' position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover.set_down())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

    #
    # TEST SET DOWN INVERTED
    #
    def test_set_down_inverted(self):
        """Test moving cover to 'down' position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            invert_position=True,
        )
        self.loop.run_until_complete(cover.set_down())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )

    #
    # TEST SET SHORT UP
    #
    def test_set_short_up(self):
        """Test moving cover 'short up'."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover.set_short_up())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )

    #
    # TEST SET UP INVERTED
    #
    def test_set_up_inverted(self):
        """Test moving cover 'short up'."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            invert_position=True,
        )
        self.loop.run_until_complete(cover.set_short_up())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

    #
    # TEST SET SHORT DOWN
    #
    def test_set_down(self):
        """Test moving cover 'short down'."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover.set_short_down())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

    #
    # TEST STOP
    #
    def test_stop(self):
        """Test stopping cover."""
        xknx = XKNX()
        cover_short_stop = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        # Attempt stopping while not actually moving
        self.loop.run_until_complete(cover_short_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 0)

        # Attempt stopping while moving down
        cover_short_stop.travelcalculator.set_position(0)
        self.loop.run_until_complete(cover_short_stop.set_down())
        self.loop.run_until_complete(cover_short_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

        # Attempt stopping while moving up
        cover_short_stop.travelcalculator.set_position(100)
        self.loop.run_until_complete(cover_short_stop.set_up())
        self.loop.run_until_complete(cover_short_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )

        cover_manual_stop = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_stop="1/2/0",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover_manual_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/0"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

    def test_stop_angle(self):
        """Test stopping cover during angle move / tilting."""
        xknx = XKNX()
        cover_short_stop = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_angle="1/2/5",
            group_address_angle_state="1/2/6",
        )
        # Attempt stopping while not actually tilting
        self.loop.run_until_complete(cover_short_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 0)

        # Set cover tilt to a dummy start value, since otherwise we cannot
        # determine later on a tilt direction and without it, stopping the
        # til process has no effect.
        self.loop.run_until_complete(
            cover_short_stop.angle.process(
                Telegram(
                    destination_address=GroupAddress("1/2/5"),
                    payload=GroupValueWrite(DPTArray(0xAA)),
                )
            )
        )

        # Attempt stopping while tilting down
        self.loop.run_until_complete(cover_short_stop.set_angle(100))
        self.loop.run_until_complete(cover_short_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram = xknx.telegrams.get_nowait()
        print(telegram)
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray(0xFF)),
            ),
        )
        telegram = xknx.telegrams.get_nowait()
        print(telegram)
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

        # Attempt stopping while tilting up
        self.loop.run_until_complete(cover_short_stop.set_angle(0))
        self.loop.run_until_complete(cover_short_stop.stop())
        self.assertEqual(xknx.telegrams.qsize(), 2)
        telegram = xknx.telegrams.get_nowait()
        print(telegram)
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/5"),
                payload=GroupValueWrite(DPTArray(0x00)),
            ),
        )
        telegram = xknx.telegrams.get_nowait()
        print(telegram)
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/2"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )

    #
    # TEST POSITION
    #
    def test_position(self):
        """Test moving cover to absolute position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        self.loop.run_until_complete(cover.set_position(50))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/3"),
                payload=GroupValueWrite(DPTArray(0x80)),
            ),
        )

    def test_position_without_position_address_up(self):
        """Test moving cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )
        cover.travelcalculator.set_position(60)
        self.loop.run_until_complete(cover.set_position(50))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        # DPT 1.008 - 0:up 1:down
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )
        self.assertEqual(cover.travelcalculator.travel_to_position, 50)
        self.assertTrue(cover.is_opening())
        # process the outgoing telegram to make sure it doesn't overwrite the target position
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.travelcalculator.travel_to_position, 50)
        self.assertEqual(xknx.telegrams.qsize(), 0)

    def test_position_without_position_address_down(self):
        """Test moving cover down - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )
        cover.travelcalculator.set_position(70)
        self.loop.run_until_complete(cover.set_position(80))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )
        self.assertEqual(cover.travelcalculator.travel_to_position, 80)
        self.assertTrue(cover.is_closing())
        # process the outgoing telegram to make sure it doesn't overwrite the target position
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.travelcalculator.travel_to_position, 80)

    def test_position_without_position_address_uninitialized_up(self):
        """Test moving uninitialized cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )

        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(cover.set_position(50))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Current position unknown. Initialize cover by moving to end position."
            )

        self.loop.run_until_complete(cover.set_position(0))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(0)),
            ),
        )

    def test_position_without_position_address_uninitialized_down(self):
        """Test moving uninitialized cover to absolute position - with no absolute positioning supported."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position_state="1/2/4",
        )

        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(cover.set_position(50))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Current position unknown. Initialize cover by moving to end position."
            )

        self.loop.run_until_complete(cover.set_position(100))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/2/1"),
                payload=GroupValueWrite(DPTBinary(1)),
            ),
        )

    def test_angle(self):
        """Test changing angle."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
            group_address_position_state="1/4/17",
            group_address_position="1/4/16",
            group_address_angle="1/4/18",
            group_address_angle_state="1/4/19",
        )
        self.loop.run_until_complete(cover.set_angle(50))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                destination_address=GroupAddress("1/4/18"),
                payload=GroupValueWrite(DPTArray(0x80)),
            ),
        )

    def test_angle_not_supported(self):
        """Test changing angle on cover which does not support angle."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "Children.Venetian",
            group_address_long="1/4/14",
            group_address_short="1/4/15",
        )
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(cover.set_angle(50))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Angle not supported for device %s", "Children.Venetian"
            )

    #
    # TEST PROCESS
    #
    def test_process_position(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
        )
        # initial position process - position is unknown so this is the new state - not moving
        telegram = Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTArray(213))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.current_position(), 84)
        self.assertFalse(cover.is_traveling())
        # state telegram updates current position - we are not moving so this is new state - not moving
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(42))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.current_position(), 16)
        self.assertFalse(cover.is_traveling())
        self.assertEqual(cover.travelcalculator.travel_to_position, 16)
        # new position - movement starts
        telegram = Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTArray(255))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.current_position(), 16)
        self.assertTrue(cover.is_closing())
        self.assertEqual(cover.travelcalculator.travel_to_position, 100)
        # new state while moving - movement goes on; travelcalculator updated
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(213))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.current_position(), 84)
        self.assertTrue(cover.is_closing())
        self.assertEqual(cover.travelcalculator.travel_to_position, 100)

    def test_process_angle(self):
        """Test process / reading telegrams from telegram queue. Test if position is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_angle="1/2/3",
            group_address_angle_state="1/2/4",
        )
        telegram = Telegram(
            GroupAddress("1/2/4"), payload=GroupValueWrite(DPTArray(42))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertEqual(cover.current_angle(), 16)

    def test_process_up(self):
        """Test process / reading telegrams from telegram queue. Test if up/down is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx, "TestCover", group_address_long="1/2/1", group_address_short="1/2/2"
        )
        cover.travelcalculator.set_position(50)
        self.assertFalse(cover.is_traveling())
        telegram = Telegram(
            GroupAddress("1/2/1"), payload=GroupValueWrite(DPTBinary(0))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertTrue(cover.is_opening())

    def test_process_down(self):
        """Test process / reading telegrams from telegram queue. Test if up/down is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx, "TestCover", group_address_long="1/2/1", group_address_short="1/2/2"
        )
        cover.travelcalculator.set_position(50)
        self.assertFalse(cover.is_traveling())
        telegram = Telegram(
            GroupAddress("1/2/1"), payload=GroupValueWrite(DPTBinary(1))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertTrue(cover.is_closing())

    def test_process_stop(self):
        """Test process / reading telegrams from telegram queue. Test if stop is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
        )
        cover.travelcalculator.set_position(50)
        self.loop.run_until_complete(cover.set_down())
        self.assertTrue(cover.is_traveling())
        telegram = Telegram(
            GroupAddress("1/2/2"), payload=GroupValueWrite(DPTBinary(1))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertFalse(cover.is_traveling())

    def test_process_short_stop(self):
        """Test process / reading telegrams from telegram queue. Test if stop is processed correctly."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
        )
        cover.travelcalculator.set_position(50)
        self.loop.run_until_complete(cover.set_down())
        self.assertTrue(cover.is_traveling())
        telegram = Telegram(
            GroupAddress("1/2/2"), payload=GroupValueWrite(DPTBinary(1))
        )
        self.loop.run_until_complete(cover.process(telegram))
        self.assertFalse(cover.is_traveling())

    def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback is executed."""
        # pylint: disable=no-self-use
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_stop="1/2/3",
            group_address_position="1/2/4",
            group_address_position_state="1/2/5",
            group_address_angle="1/2/6",
            group_address_angle_state="1/2/7",
        )

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        cover.register_device_updated_cb(async_after_update_callback)
        for address, payload, feature in [
            ("1/2/1", DPTBinary(1), "long"),
            ("1/2/2", DPTBinary(1), "short"),
            ("1/2/4", DPTArray(42), "position"),
            ("1/2/5", DPTArray(42), "position state"),
            ("1/2/6", DPTArray(42), "angle"),
            ("1/2/7", DPTArray(51), "angle state"),
        ]:
            with self.subTest(address=address, feature=feature):
                telegram = Telegram(
                    destination_address=GroupAddress(address),
                    payload=GroupValueWrite(payload),
                )
                self.loop.run_until_complete(cover.process(telegram))
                after_update_callback.assert_called_with(cover)
                after_update_callback.reset_mock()
        # Stop only when cover is travelling
        telegram = Telegram(
            GroupAddress("1/2/3"), payload=GroupValueWrite(DPTBinary(1))
        )
        self.loop.run_until_complete(cover.process(telegram))
        after_update_callback.assert_not_called()
        self.loop.run_until_complete(cover.set_down())
        self.loop.run_until_complete(cover.process(telegram))
        after_update_callback.assert_called_with(cover)

    #
    # IS TRAVELING / IS UP / IS DOWN
    #
    def test_is_traveling(self):
        """Test moving cover to absolute position."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            travel_time_down=10,
            travel_time_up=10,
        )
        with patch("time.time") as mock_time:
            mock_time.return_value = 1517000000.0
            self.assertFalse(cover.is_traveling())
            self.assertFalse(cover.is_opening())
            self.assertFalse(cover.is_closing())
            self.assertTrue(cover.position_reached())
            # we start with state open covers (up)
            cover.travelcalculator.set_position(0)
            self.loop.run_until_complete(cover.set_down())
            self.assertTrue(cover.is_traveling())
            self.assertTrue(cover.is_open())
            self.assertFalse(cover.is_closed())
            self.assertFalse(cover.is_opening())
            self.assertTrue(cover.is_closing())

            mock_time.return_value = 1517000005.0  # 5 Seconds, half way
            self.assertFalse(cover.position_reached())
            self.assertTrue(cover.is_traveling())
            self.assertFalse(cover.is_open())
            self.assertFalse(cover.is_closed())
            self.assertFalse(cover.is_opening())
            self.assertTrue(cover.is_closing())

            mock_time.return_value = 1517000010.0  # 10 Seconds, fully closed
            self.assertTrue(cover.position_reached())
            self.assertFalse(cover.is_traveling())
            self.assertFalse(cover.is_open())
            self.assertTrue(cover.is_closed())
            self.assertFalse(cover.is_opening())
            self.assertFalse(cover.is_closing())
            # up again
            self.loop.run_until_complete(cover.set_up())
            self.assertFalse(cover.position_reached())
            self.assertTrue(cover.is_traveling())
            self.assertFalse(cover.is_open())
            self.assertTrue(cover.is_closed())
            self.assertTrue(cover.is_opening())
            self.assertFalse(cover.is_closing())

            mock_time.return_value = 1517000015.0  # 15 Seconds, half way
            self.assertFalse(cover.position_reached())
            self.assertTrue(cover.is_traveling())
            self.assertFalse(cover.is_open())
            self.assertFalse(cover.is_closed())
            self.assertTrue(cover.is_opening())
            self.assertFalse(cover.is_closing())

            mock_time.return_value = 1517000016.0  # 16 Seconds, manual stop
            self.loop.run_until_complete(cover.stop())
            self.assertTrue(cover.position_reached())
            self.assertFalse(cover.is_traveling())
            self.assertFalse(cover.is_open())
            self.assertFalse(cover.is_closed())
            self.assertFalse(cover.is_opening())
            self.assertFalse(cover.is_closing())

    #
    # TEST AUTO STOP
    #
    def test_auto_stop(self):
        """Test auto stop functionality."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_stop="1/2/2",
            travel_time_down=10,
            travel_time_up=10,
        )
        with patch("xknx.devices.Cover.stop") as mock_stop, patch(
            "time.time"
        ) as mock_time:
            fut = asyncio.Future()
            fut.set_result(None)
            mock_stop.return_value = fut

            mock_time.return_value = 1517000000.0
            # we start with state 0 - open covers (up) this is assumed immediately
            self.loop.run_until_complete(cover.set_position(0))

            self.loop.run_until_complete(cover.set_position(50))

            mock_time.return_value = 1517000001.0
            self.loop.run_until_complete(cover.auto_stop_if_necessary())
            mock_stop.assert_not_called()

            mock_time.return_value = 1517000005.0
            self.loop.run_until_complete(cover.auto_stop_if_necessary())
            mock_stop.assert_called_with()
            mock_stop.reset_mock()

    #
    # TEST DO
    #
    def test_do(self):
        """Test 'do' functionality."""

        async def async_none():
            return None

        xknx = XKNX()
        cover = Cover(xknx, "TestCover")
        with patch("xknx.devices.Cover.set_up") as mock:
            mock.return_value = asyncio.ensure_future(async_none())
            self.loop.run_until_complete(cover.do("up"))
            mock.assert_called_once_with()
        with patch("xknx.devices.Cover.set_short_up") as mock:
            mock.return_value = asyncio.ensure_future(async_none())
            self.loop.run_until_complete(cover.do("short_up"))
            mock.assert_called_once_with()
        with patch("xknx.devices.Cover.set_down") as mock:
            mock.return_value = asyncio.ensure_future(async_none())
            self.loop.run_until_complete(cover.do("down"))
            mock.assert_called_once_with()
        with patch("xknx.devices.Cover.set_short_down") as mock:
            mock.return_value = asyncio.ensure_future(async_none())
            self.loop.run_until_complete(cover.do("short_down"))
            mock.assert_called_once_with()
        with patch("xknx.devices.Cover.stop") as mock:
            mock.return_value = asyncio.ensure_future(async_none())
            self.loop.run_until_complete(cover.do("stop"))
            mock.assert_called_once_with()

    def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        cover = Cover(xknx, "TestCover")
        with patch("logging.Logger.warning") as mock_warn:
            self.loop.run_until_complete(cover.do("execute"))
            self.assertEqual(xknx.telegrams.qsize(), 0)
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "TestCover"
            )

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX()
        cover = Cover(
            xknx,
            "TestCover",
            group_address_long="1/2/1",
            group_address_short="1/2/2",
            group_address_position="1/2/3",
            group_address_position_state="1/2/4",
            group_address_angle="1/2/5",
            group_address_angle_state="1/2/6",
        )

        self.assertTrue(cover.has_group_address(GroupAddress("1/2/1")))
        self.assertTrue(cover.has_group_address(GroupAddress("1/2/2")))
        self.assertTrue(cover.has_group_address(GroupAddress("1/2/3")))
        self.assertTrue(cover.has_group_address(GroupAddress("1/2/4")))
        self.assertTrue(cover.has_group_address(GroupAddress("1/2/5")))
        self.assertTrue(cover.has_group_address(GroupAddress("1/2/6")))
        self.assertFalse(cover.has_group_address(GroupAddress("1/2/7")))
