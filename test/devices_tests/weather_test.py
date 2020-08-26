"""Unit test for Weather objects."""
import asyncio
import unittest
from unittest.mock import Mock

from xknx import XKNX
from xknx.devices import Weather
from xknx.dpt import DPTArray
from xknx.telegram import GroupAddress, Telegram, TelegramType


class TestWeather(unittest.TestCase):
    """Test class for Weather objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    #
    # STR FUNCTIONS
    #

    def test_str_temperature(self):
        """Test resolve state with temperature."""
        xknx = XKNX(loop=self.loop)
        weather = Weather(name="weather",
                          xknx=xknx,
                          group_address_temperature="1/3/4")
        weather._temperature.payload = DPTArray((0x19, 0xa))

        self.assertEqual(weather.temperature, 21.28)
        self.assertEqual(weather._temperature.unit_of_measurement, "°C")
        self.assertEqual(weather._temperature.ha_device_class, "temperature")

    #
    # GENERATOR _iter_remote_values
    #
    def test_iter_remote_values(self):
        """Test sensor has group address."""
        xknx = XKNX(loop=self.loop)
        weather = Weather(name="weather",
                          xknx=xknx,
                          group_address_temperature="1/3/4",
                          group_address_rain_alarm='1/4/5',
                          group_address_brightness_south='7/7/0')
        self.assertTrue(weather.has_group_address(GroupAddress('1/3/4')))
        self.assertTrue(weather.has_group_address(GroupAddress('7/7/0')))
        self.assertTrue(weather.has_group_address(GroupAddress('1/4/5')))
        self.assertFalse(weather.has_group_address(GroupAddress('1/2/4')))

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX(loop=self.loop)
        weather = Weather(name="weather",
                          xknx=xknx,
                          group_address_temperature="1/3/4")
        self.assertTrue(weather._temperature.has_group_address(GroupAddress('1/3/4')))
        self.assertFalse(weather._temperature.has_group_address(GroupAddress('1/2/4')))
