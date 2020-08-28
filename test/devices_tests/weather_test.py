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

    def test_temperature(self):
        """Test resolve state with temperature."""
        xknx = XKNX(loop=self.loop)
        weather = Weather(name="weather",
                          xknx=xknx,
                          group_address_temperature="1/3/4")
        weather._temperature.payload = DPTArray((0x19, 0xa))

        self.assertTrue(weather.has_group_address(GroupAddress('1/3/4')))
        self.assertEqual(weather.temperature, 21.28)
        self.assertEqual(weather._temperature.unit_of_measurement, "°C")
        self.assertEqual(weather._temperature.ha_device_class, "temperature")

    def test_brightness(self):
        """Test resolve state for brightness east, west and south."""
        xknx = XKNX(loop=self.loop)
        weather: Weather = Weather(name="weather",
                                   xknx=xknx,
                                   group_address_brightness_east="1/3/5",
                                   group_address_brightness_south="1/3/6",
                                   group_address_brightness_west="1/3/7")

        weather._brightness_east.payload = DPTArray((0x7C, 0x5E,))
        weather._brightness_west.payload = DPTArray((0x7C, 0x5C,))
        weather._brightness_south.payload = DPTArray((0x7C, 0x5A,))

        self.assertEqual(weather.brightness_east, 366346.24)
        self.assertEqual(weather._brightness_east.unit_of_measurement, "lx")
        self.assertEqual(weather._brightness_east.ha_device_class, 'illuminance')

        self.assertEqual(weather.brightness_west, 365690.88)
        self.assertEqual(weather._brightness_west.unit_of_measurement, "lx")
        self.assertEqual(weather._brightness_west.ha_device_class, 'illuminance')

        self.assertEqual(weather.brightness_south, 365035.52)
        self.assertEqual(weather._brightness_south.unit_of_measurement, "lx")
        self.assertEqual(weather._brightness_south.ha_device_class, 'illuminance')

    def test_wind_speed(self):
        """Test wind speed received."""
        xknx = XKNX(loop=self.loop)
        weather: Weather = Weather(name="weather",
                                   xknx=xknx,
                                   group_address_brightness_east="1/3/8")

        weather._wind_speed.payload = DPTArray((0x7D, 0x98,))

        self.assertEqual(weather.wind_speed, 469237.76)
        self.assertEqual(weather._wind_speed.unit_of_measurement, "m/s")
        self.assertEqual(weather._wind_speed.ha_device_class, None)

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
