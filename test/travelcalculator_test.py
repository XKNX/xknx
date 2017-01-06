import unittest
import time
from xknx import TravelCalculator

class TestTravelCalculator(unittest.TestCase):

    # TravelCalculator(64, 128) means:
    #
    #     4 steps / sec UP
    #     2 steps / sec DOWN
    #
    # INIT
    #
    def test_time_default(self):
        travelcalculator = TravelCalculator(64, 128)
        self.assertLess(
            abs(time.time()-travelcalculator.current_time()),
            0.001)

    def test_time_set_from_outside(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.time_set_from_outside = 1000
        self.assertEqual(travelcalculator.current_time(), 1000)

    def test_set_position(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(128)
        self.assertTrue(travelcalculator.position_reached())
        self.assertEqual(travelcalculator.current_position(), 128)

    def test_set_position_after_travel(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.start_travel(100)
        travelcalculator.set_position(128)
        self.assertTrue(travelcalculator.position_reached())
        self.assertEqual(travelcalculator.current_position(), 128)

    def test_travel_up(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(100)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(120)

        #time not changed, still at beginning
        self.assertEqual(travelcalculator.current_position(), 100)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 1
        self.assertEqual(travelcalculator.current_position(), 104)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 2
        self.assertEqual(travelcalculator.current_position(), 108)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 116)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 5

        # position reached
        self.assertEqual(travelcalculator.current_position(), 120)
        self.assertTrue(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 10
        self.assertEqual(travelcalculator.current_position(), 120)
        self.assertTrue(travelcalculator.position_reached())

    def test_travel_down(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(120)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(100)

        # time not changed, still at beginning
        self.assertEqual(travelcalculator.current_position(), 120)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 2
        self.assertEqual(travelcalculator.current_position(), 116)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 112)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 8
        self.assertEqual(travelcalculator.current_position(), 104)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 10
        # position reached
        self.assertEqual(travelcalculator.current_position(), 100)
        self.assertTrue(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 20
        self.assertEqual(travelcalculator.current_position(), 100)
        self.assertTrue(travelcalculator.position_reached())

    def test_stop(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(120)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(100)

        # stop aftert two seconds
        travelcalculator.time_set_from_outside = 1000 + 2
        travelcalculator.stop()

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 116)
        self.assertTrue(travelcalculator.position_reached())

        # restart after 1 second
        travelcalculator.time_set_from_outside = 1000 + 3
        travelcalculator.start_travel(130)

        # running up for 3 seconds
        travelcalculator.time_set_from_outside = 1000 + 6
        self.assertEqual(travelcalculator.current_position(), 128)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 7
        self.assertEqual(travelcalculator.current_position(), 130)
        self.assertTrue(travelcalculator.position_reached())


    def test_change_direction(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(120)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel(100)

        # change direction after two seconds
        travelcalculator.time_set_from_outside = 1000 + 2
        travelcalculator.start_travel(130)

        self.assertEqual(travelcalculator.current_position(), 116)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 4
        self.assertEqual(travelcalculator.current_position(), 124)
        self.assertFalse(travelcalculator.position_reached())

        travelcalculator.time_set_from_outside = 1000 + 6
        self.assertEqual(travelcalculator.current_position(), 130)
        self.assertTrue(travelcalculator.position_reached())

    def test_travel_full_up(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(128)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel_up()

        travelcalculator.time_set_from_outside = 1063
        self.assertFalse(travelcalculator.position_reached())
        self.assertFalse(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_open())

        travelcalculator.time_set_from_outside = 1064
        self.assertTrue(travelcalculator.position_reached())
        self.assertTrue(travelcalculator.is_open())
        self.assertFalse(travelcalculator.is_closed())

    def test_travel_full_down(self):
        travelcalculator = TravelCalculator(64, 128)
        travelcalculator.set_position(128)

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel_down()

        travelcalculator.time_set_from_outside = 1031
        self.assertFalse(travelcalculator.position_reached())
        self.assertFalse(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_open())

        travelcalculator.time_set_from_outside = 1032
        self.assertTrue(travelcalculator.position_reached())
        self.assertTrue(travelcalculator.is_closed())
        self.assertFalse(travelcalculator.is_open())

    def test_is_travelling(self):
        travelcalculator = TravelCalculator(64, 128)
        self.assertFalse(travelcalculator.is_travelling())

        travelcalculator.set_position(128)
        self.assertFalse(travelcalculator.is_travelling())

        travelcalculator.time_set_from_outside = 1000
        travelcalculator.start_travel_down()

        travelcalculator.time_set_from_outside = 1001
        self.assertTrue(travelcalculator.is_travelling())

        travelcalculator.time_set_from_outside = 1032
        self.assertFalse(travelcalculator.is_travelling())

SUITE = unittest.TestLoader().loadTestsFromTestCase(TestTravelCalculator)
unittest.TextTestRunner(verbosity=2).run(SUITE)
