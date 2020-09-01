"""Unit test for TravelCalculator objects."""
import unittest
from unittest.mock import patch

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
    def test_init(self):
        """Test initial status."""
        travelcalculator = TravelCalculator(25, 50)
        self.assertFalse(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_closing())
        self.assertFalse(travelcalculator.is_opening())
        self.assertFalse(travelcalculator.is_traveling())
        self.assertTrue(travelcalculator.position_reached())
        self.assertIsNone(travelcalculator.current_position())

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
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(40)
            travelcalculator.start_travel(60)

            # time not changed, still at beginning
            self.assertEqual(travelcalculator.current_position(), 40)
            self.assertFalse(travelcalculator.position_reached())
            self.assertEqual(
                travelcalculator.travel_direction, TravelStatus.DIRECTION_DOWN
            )

            mock_time.return_value = 1580000001.0
            self.assertEqual(travelcalculator.current_position(), 44)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000002.0
            self.assertEqual(travelcalculator.current_position(), 48)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000004.0
            self.assertEqual(travelcalculator.current_position(), 56)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000005.0
            # position reached
            self.assertEqual(travelcalculator.current_position(), 60)
            self.assertTrue(travelcalculator.position_reached())

            mock_time.return_value = 1580000010.0
            self.assertEqual(travelcalculator.current_position(), 60)
            self.assertTrue(travelcalculator.position_reached())

    def test_travel_up(self):
        """Test travel down."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(70)
            travelcalculator.start_travel(50)

            # time not changed, still at beginning
            self.assertEqual(travelcalculator.current_position(), 70)
            self.assertFalse(travelcalculator.position_reached())
            self.assertEqual(
                travelcalculator.travel_direction, TravelStatus.DIRECTION_UP
            )

            mock_time.return_value = 1580000002.0
            self.assertEqual(travelcalculator.current_position(), 66)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000004.0
            self.assertEqual(travelcalculator.current_position(), 62)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000008.0
            self.assertEqual(travelcalculator.current_position(), 54)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000010.0
            # position reached
            self.assertEqual(travelcalculator.current_position(), 50)
            self.assertTrue(travelcalculator.position_reached())

            mock_time.return_value = 1580000020.0
            self.assertEqual(travelcalculator.current_position(), 50)
            self.assertTrue(travelcalculator.position_reached())

    def test_stop(self):
        """Test stopping."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(80)
            travelcalculator.start_travel(60)

            self.assertEqual(
                travelcalculator.travel_direction, TravelStatus.DIRECTION_UP
            )

            # stop aftert two seconds
            mock_time.return_value = 1580000002.0
            travelcalculator.stop()

            mock_time.return_value = 1580000004.0
            self.assertEqual(travelcalculator.current_position(), 76)
            self.assertTrue(travelcalculator.position_reached())

            # restart after 1 additional second (3 seconds)
            mock_time.return_value = 1580000005.0
            travelcalculator.start_travel(68)

            # running up for 6 seconds
            mock_time.return_value = 1580000006.0
            self.assertEqual(travelcalculator.current_position(), 74)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000009.0
            self.assertEqual(travelcalculator.current_position(), 68)
            self.assertTrue(travelcalculator.position_reached())

    def test_change_direction(self):
        """Test changing direction while travelling."""
        travelcalculator = TravelCalculator(50, 25)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(60)
            travelcalculator.start_travel(80)
            self.assertEqual(
                travelcalculator.travel_direction, TravelStatus.DIRECTION_DOWN
            )

            # change direction after two seconds
            mock_time.return_value = 1580000002.0
            self.assertEqual(travelcalculator.current_position(), 64)
            travelcalculator.start_travel(48)
            self.assertEqual(
                travelcalculator.travel_direction, TravelStatus.DIRECTION_UP
            )

            self.assertEqual(travelcalculator.current_position(), 64)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000004.0
            self.assertEqual(travelcalculator.current_position(), 56)
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000006.0
            self.assertEqual(travelcalculator.current_position(), 48)
            self.assertTrue(travelcalculator.position_reached())

    def test_travel_full_up(self):
        """Test travelling to the full up position."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(30)
            travelcalculator.start_travel_up()

            mock_time.return_value = 1580000014.0
            self.assertFalse(travelcalculator.position_reached())
            self.assertFalse(travelcalculator.is_closed())
            self.assertFalse(travelcalculator.is_open())

            mock_time.return_value = 1580000015.0
            self.assertTrue(travelcalculator.position_reached())
            self.assertTrue(travelcalculator.is_open())
            self.assertFalse(travelcalculator.is_closed())

    def test_travel_full_down(self):
        """Test travelling to the full down position."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            travelcalculator.set_position(20)
            travelcalculator.start_travel_down()

            mock_time.return_value = 1580000019.0
            self.assertFalse(travelcalculator.position_reached())
            self.assertFalse(travelcalculator.is_closed())
            self.assertFalse(travelcalculator.is_open())

            mock_time.return_value = 1580000020.0
            self.assertTrue(travelcalculator.position_reached())
            self.assertTrue(travelcalculator.is_closed())
            self.assertFalse(travelcalculator.is_open())

    def test_is_traveling(self):
        """Test if cover is traveling and position reached."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            self.assertFalse(travelcalculator.is_traveling())
            self.assertTrue(travelcalculator.position_reached())

            travelcalculator.set_position(80)
            self.assertFalse(travelcalculator.is_traveling())
            self.assertTrue(travelcalculator.position_reached())

            mock_time.return_value = 1580000000.0
            travelcalculator.start_travel_down()

            mock_time.return_value = 1580000004.0
            self.assertTrue(travelcalculator.is_traveling())
            self.assertFalse(travelcalculator.position_reached())

            mock_time.return_value = 1580000005.0
            self.assertFalse(travelcalculator.is_traveling())
            self.assertTrue(travelcalculator.position_reached())

    def test_is_opening_closing(self):
        """Test reports is_opening and is_closing."""
        travelcalculator = TravelCalculator(25, 50)
        with patch("time.time") as mock_time:
            mock_time.return_value = 1580000000.0
            self.assertFalse(travelcalculator.is_opening())
            self.assertFalse(travelcalculator.is_closing())

            travelcalculator.set_position(80)
            self.assertFalse(travelcalculator.is_opening())
            self.assertFalse(travelcalculator.is_closing())

            mock_time.return_value = 1580000000.0
            travelcalculator.start_travel_down()
            self.assertFalse(travelcalculator.is_opening())
            self.assertTrue(travelcalculator.is_closing())

            mock_time.return_value = 1580000004.0
            self.assertFalse(travelcalculator.is_opening())
            self.assertTrue(travelcalculator.is_closing())

            mock_time.return_value = 1580000005.0
            self.assertFalse(travelcalculator.is_opening())
            self.assertFalse(travelcalculator.is_closing())
            # up direction
            travelcalculator.start_travel(50)
            self.assertTrue(travelcalculator.is_opening())
            self.assertFalse(travelcalculator.is_closing())

            mock_time.return_value = 1580000030.0
            self.assertFalse(travelcalculator.is_opening())
            self.assertFalse(travelcalculator.is_closing())
