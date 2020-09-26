"""Unit test for Weather objects."""
import asyncio
import datetime
import unittest

from xknx import XKNX
from xknx.devices import Weather
from xknx.devices.weather import WeatherCondition
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress


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
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_temperature="1/3/4")
        weather._temperature.payload = DPTArray((0x19, 0xA))

        self.assertTrue(weather.has_group_address(GroupAddress("1/3/4")))
        self.assertEqual(weather.temperature, 21.28)
        self.assertEqual(weather._temperature.unit_of_measurement, "°C")
        self.assertEqual(weather._temperature.ha_device_class, "temperature")

    def test_brightness(self):
        """Test resolve state for brightness east, west and south."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
        )

        weather._brightness_east.payload = DPTArray(
            (
                0x7C,
                0x5E,
            )
        )
        weather._brightness_west.payload = DPTArray(
            (
                0x7C,
                0x5C,
            )
        )
        weather._brightness_south.payload = DPTArray(
            (
                0x7C,
                0x5A,
            )
        )

        self.assertEqual(weather.brightness_east, 366346.24)
        self.assertEqual(weather._brightness_east.unit_of_measurement, "lx")
        self.assertEqual(weather._brightness_east.ha_device_class, "illuminance")

        self.assertEqual(weather.brightness_west, 365690.88)
        self.assertEqual(weather._brightness_west.unit_of_measurement, "lx")
        self.assertEqual(weather._brightness_west.ha_device_class, "illuminance")

        self.assertEqual(weather.brightness_south, 365035.52)
        self.assertEqual(weather._brightness_south.unit_of_measurement, "lx")
        self.assertEqual(weather._brightness_south.ha_device_class, "illuminance")

    def test_pressure(self):
        """Test resolve state with pressure."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_air_pressure="1/3/4")
        weather._air_pressure.payload = DPTArray((0x6C, 0xAD))

        self.assertEqual(weather.air_pressure, 98058.24)
        self.assertEqual(weather._air_pressure.unit_of_measurement, "Pa")
        self.assertEqual(weather._air_pressure.ha_device_class, "pressure")

    def test_humidity(self):
        """Test humidity."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_humidity="1/2/4")
        weather._humidity.payload = DPTArray(
            (
                0x7E,
                0xE1,
            )
        )

        self.assertEqual(weather.humidity, 577044.48)
        self.assertEqual(weather._humidity.unit_of_measurement, "%")
        self.assertEqual(weather._humidity.ha_device_class, "humidity")

    def test_wind_speed(self):
        """Test wind speed received."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather", xknx=xknx, group_address_brightness_east="1/3/8"
        )

        weather._wind_speed.payload = DPTArray(
            (
                0x7D,
                0x98,
            )
        )

        self.assertEqual(weather.wind_speed, 469237.76)
        self.assertEqual(weather._wind_speed.unit_of_measurement, "m/s")
        self.assertEqual(weather._wind_speed.ha_device_class, None)

    def test_state_lightning(self):
        """Test current_state returns lightning if wind alarm and rain alarm are true."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_rain_alarm="1/3/8",
            group_address_wind_alarm="1/3/9",
        )

        weather._rain_alarm.payload = DPTBinary(1)
        weather._wind_alarm.payload = DPTBinary(1)

        self.assertEqual(weather.ha_current_state(), WeatherCondition.lightning_rainy)

    def test_state_snowy_rainy(self):
        """Test snow rain if frost alarm and rain alarm are true."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_rain_alarm="1/3/8",
            group_address_frost_alarm="1/3/10",
        )

        weather._rain_alarm.payload = DPTBinary(1)
        weather._frost_alarm.payload = DPTBinary(1)

        self.assertEqual(weather.ha_current_state(), WeatherCondition.snowy_rainy)

    def test_wind_alarm(self):
        """Test basic state mapping."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_rain_alarm="1/3/8",
            group_address_wind_alarm="1/3/9",
            group_address_frost_alarm="1/3/10",
        )

        weather._wind_alarm.payload = DPTBinary(1)

        self.assertEqual(weather.ha_current_state(), WeatherCondition.windy)

    def test_rain_alarm(self):
        """Test basic state mapping."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_rain_alarm="1/3/8",
            group_address_wind_alarm="1/3/9",
            group_address_frost_alarm="1/3/10",
        )

        weather._rain_alarm.payload = DPTBinary(1)

        self.assertEqual(weather.ha_current_state(), WeatherCondition.rainy)

    def test_cloudy_summer(self):
        """Test cloudy summer if illuminance matches defined interval."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
        )

        weather._brightness_south.payload = DPTArray(
            (
                0x46,
                0x45,
            )
        )

        summer_date = datetime.datetime(2020, 10, 5, 18, 00)

        self.assertEqual(
            weather.ha_current_state(current_date=summer_date), WeatherCondition.cloudy
        )

    def test_sunny_summer(self):
        """Test returns sunny condition if illuminance is in defined interval"""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
        )

        weather._brightness_south.payload = DPTArray(
            (
                0x7C,
                0x5C,
            )
        )

        summer_date = datetime.datetime(2020, 10, 5, 18, 00)

        self.assertEqual(
            weather.ha_current_state(current_date=summer_date), WeatherCondition.sunny
        )

    def test_sunny_winter(self):
        """Test sunny winter if illuminance matches defined interval."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
        )

        weather._brightness_south.payload = DPTArray(
            (
                0x7C,
                0x5C,
            )
        )

        winter_date = datetime.datetime(2020, 12, 5, 18, 00)

        self.assertEqual(
            weather.ha_current_state(current_date=winter_date), WeatherCondition.sunny
        )

    def test_cloudy_winter(self):
        """Test cloudy winter if illuminance matches defined interval."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
        )

        weather._brightness_south.payload = DPTArray(
            (
                0x46,
                0x45,
            )
        )

        winter_date = datetime.datetime(2020, 12, 31, 18, 00)

        self.assertEqual(
            weather.ha_current_state(current_date=winter_date), WeatherCondition.cloudy
        )

    def test_day_night(self):
        """Test day night mapping."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather", xknx=xknx, group_address_day_night="1/3/20"
        )

        weather._day_night.payload = DPTBinary(0)

        self.assertEqual(weather.ha_current_state(), WeatherCondition.clear_night)

    def test_weather_default(self):
        """Test default state mapping."""
        xknx = XKNX()
        weather: Weather = Weather(name="weather", xknx=xknx)

        self.assertEqual(weather.ha_current_state(), WeatherCondition.exceptional)

    #
    # Expose Sensor tests
    #
    def test_expose_sensor(self):
        """Test default state mapping."""
        xknx = XKNX()
        Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
        )

        self.assertEqual(len(xknx.devices), 1)

        Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
            group_address_wind_alarm="1/5/4",
            expose_sensors=True,
        )

        self.assertEqual(len(xknx.devices), 6)

    #
    # GENERATOR _iter_remote_values
    #
    def test_iter_remote_values(self):
        """Test sensor has group address."""
        xknx = XKNX()
        weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_temperature="1/3/4",
            group_address_rain_alarm="1/4/5",
            group_address_brightness_south="7/7/0",
        )
        self.assertTrue(weather.has_group_address(GroupAddress("1/3/4")))
        self.assertTrue(weather.has_group_address(GroupAddress("7/7/0")))
        self.assertTrue(weather.has_group_address(GroupAddress("1/4/5")))
        self.assertFalse(weather.has_group_address(GroupAddress("1/2/4")))

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_temperature="1/3/4")
        self.assertTrue(weather._temperature.has_group_address(GroupAddress("1/3/4")))
        self.assertFalse(weather._temperature.has_group_address(GroupAddress("1/2/4")))
