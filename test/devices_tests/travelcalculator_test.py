"""Unit test for TravelCalculator objects."""
import time
import unittest

from xknx.devices import TravelCalculator, TravelStatus


class TestTravelCalculator(unittest.TestCase):
    """Test class for TravelCalculator objects."""

    # TravelCalculator(25, 50) means:
    #
    #     2 steps / sec UP
    #     4 steps / sec DOWN
    #
    # INIT
    #
    def test_time_default(self):
        """Test default time settings (no time set from outside)."""
        travelcalculator = TravelCalculator(25, 50)
        self.assertLess(
            abs(time.time()-travelcalculator.current_time()),
            0.001)

    def test_time_set_from_outside(self):
        """Test setting the current time from outside."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.time_set_from_outside = 1000
        self.assertEqual(travelcalculator.current_time(), 1000)

    def test_set_position(self):
        """Test set position."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(70)
        self.assertTrue(travelcalculator.position_reached())
        self.assertEqual(travelcalculator.current_position(), 70)

    def test_set_position_after_travel(self):
        """Set explicit position after start_travel should stop traveling."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.start_travel(30)
        travelcalculator.set_position(80)
        self.assertTrue(travelcalculator.position_reached())
        self.assertEqual(travelcalculator.current_position(), 80)

    def test_travel_down(self):
        """Test travel up."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(60)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(40)

        # time not changed, still at beginning
        self.assertEqual(travelcalculator.current_position(), 60)
        self.assertFalse(travelcalculator.position_reached())
        self.assertEqual(
            travelcalculator.travel_direction,
            TravelStatus.DIRECTION_DOWN)

        travelcalculator.time_set_from_outside = 1000 + 1
        self.assertEqual(travelcalculator.current_position(), 56)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 2
        self.assertEqual(travelcalculator.current_position(), 52)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 44)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 5

        # position reached
        self.assertEqual(travelcalculator.current_position(), 40)
        self.assertTrue(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 10
        self.assertEqual(travelcalculator.current_position(), 40)
        self.assertTrue(travelcalculator.position_reached())

    def test_travel_up(self):
        """Test travel down."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(50)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(70)

        # time not changed, still at beginning
        self.assertEqual(travelcalculator.current_position(), 50)
        self.assertFalse(travelcalculator.position_reached())
        self.assertEqual(
            travelcalculator.travel_direction,
            TravelStatus.DIRECTION_UP)

        travelcalculator.time_set_from_outside = 1000 + 2
        self.assertEqual(travelcalculator.current_position(), 54)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 58)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 8
        self.assertEqual(travelcalculator.current_position(), 66)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 10
        # position reached
        self.assertEqual(travelcalculator.current_position(), 70)
        self.assertTrue(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 20
        self.assertEqual(travelcalculator.current_position(), 70)
        self.assertTrue(travelcalculator.position_reached())

    def test_stop(self):
        """Test stopping."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(60)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(80)
        self.assertEqual(
            travelcalculator.travel_direction,
            TravelStatus.DIRECTION_UP)

        # stop aftert two seconds
        travelcalculator.time_set_from_outside = 1000 + 2
        travelcalculator.stop()

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 64)
        self.assertTrue(travelcalculator.position_reached())

        # restart after 1 additional second (3 seconds)
        travelcalculator.time_set_from_outside = 1000 + 5
        travelcalculator.start_travel(68)

        # running up for 6 seconds
        travelcalculator.time_set_from_outside = 1000 + 6
        self.assertEqual(travelcalculator.current_position(), 66)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 7
        self.assertEqual(travelcalculator.current_position(), 68)
        self.assertTrue(travelcalculator.position_reached())

    def test_change_direction(self):
        """Test changing direction while travelling."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(60)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(80)
        self.assertEqual(
            travelcalculator.travel_direction,
            TravelStatus.DIRECTION_UP)

        # change direction after two seconds
        travelcalculator.time_set_from_outside = 1000 + 2
        self.assertEqual(travelcalculator.current_position(), 64)
        travelcalculator.start_travel(48)
        self.assertEqual(
            travelcalculator.travel_direction,
            TravelStatus.DIRECTION_DOWN)

        self.assertEqual(travelcalculator.current_position(), 64)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 56)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 6
        self.assertEqual(travelcalculator.current_position(), 48)
        self.assertTrue(travelcalculator.position_reached())

    def test_travel_full_up(self):
        """Test travelling to the full up position."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(70)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel_up()

        travelcalculator.time_set_from_outside = 1014
        self.assertFalse(travelcalculator.position_reached())
        self.assertFalse(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_open())

        travelcalculator.time_set_from_outside = 1015
        self.assertTrue(travelcalculator.position_reached())
        self.assertTrue(travelcalculator.is_open())
        self.assertFalse(travelcalculator.is_closed())

    def test_travel_full_down(self):
        """Test travelling to the full down position."""
        travelcalculator = TravelCalculator(25, 50)
        travelcalculator.set_position(80)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel_down()

        travelcalculator.time_set_from_outside = 1019
        self.assertFalse(travelcalculator.position_reached())
        self.assertFalse(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_open())

        travelcalculator.time_set_from_outside = 1020
        self.assertTrue(travelcalculator.position_reached())
        self.assertTrue(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_open())

    def test_is_traveling(self):
        """Test if cover is traveling."""
        travelcalculator = TravelCalculator(25, 50)
        self.assertFalse(travelcalculator.is_traveling())

        travelcalculator.set_position(20)
        self.assertFalse(travelcalculator.is_traveling())

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel_down()

        travelcalculator.time_set_from_outside = 1004
        self.assertTrue(travelcalculator.is_traveling())

        travelcalculator.time_set_from_outside = 1005
        self.assertFalse(travelcalculator.is_traveling())
