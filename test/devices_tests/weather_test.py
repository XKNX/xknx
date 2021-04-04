"""Unit test for Weather objects."""
import datetime

from xknx import XKNX
from xknx.devices import Weather
from xknx.devices.weather import WeatherCondition
from xknx.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress


class TestWeather:
    """Test class for Weather objects."""

    def test_temperature(self):
        """Test resolve state with temperature."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_temperature="1/3/4")
        weather._temperature.value = DPTArray((0x19, 0xA))

        assert weather.has_group_address(GroupAddress("1/3/4"))
        assert weather.temperature == 21.28
        assert weather._temperature.unit_of_measurement == "°C"
        assert weather._temperature.ha_device_class == "temperature"

    def test_brightness(self):
        """Test resolve state for brightness east, west and south."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
            group_address_brightness_north="1/3/8",
            group_address_temperature="1/4/4",
        )

        weather._brightness_east.value = DPTArray((0x7C, 0x5E))
        weather._brightness_west.value = DPTArray((0x7C, 0x5C))
        weather._brightness_south.value = DPTArray((0x7C, 0x5A))
        weather._brightness_north.value = DPTArray((0x7C, 0x5A))

        assert weather.brightness_east == 366346.24
        assert weather._brightness_east.unit_of_measurement == "lx"
        assert weather._brightness_east.ha_device_class == "illuminance"

        assert weather.brightness_west == 365690.88
        assert weather._brightness_west.unit_of_measurement == "lx"
        assert weather._brightness_west.ha_device_class == "illuminance"

        assert weather.brightness_south == 365035.52
        assert weather._brightness_south.unit_of_measurement == "lx"
        assert weather._brightness_south.ha_device_class == "illuminance"

        assert weather.brightness_north == 365035.52
        assert weather._brightness_north.unit_of_measurement == "lx"
        assert weather._brightness_north.ha_device_class == "illuminance"

    def test_pressure(self):
        """Test resolve state with pressure."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_air_pressure="1/3/4")
        weather._air_pressure.value = DPTArray((0x6C, 0xAD))

        assert weather.air_pressure == 98058.24
        assert weather._air_pressure.unit_of_measurement == "Pa"
        assert weather._air_pressure.ha_device_class == "pressure"

    def test_humidity(self):
        """Test humidity."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_humidity="1/2/4")
        weather._humidity.value = DPTArray((0x7E, 0xE1))

        assert weather.humidity == 577044.48
        assert weather._humidity.unit_of_measurement == "%"
        assert weather._humidity.ha_device_class == "humidity"

    def test_wind_speed(self):
        """Test wind speed received."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather", xknx=xknx, group_address_brightness_east="1/3/8"
        )

        weather._wind_speed.value = DPTArray((0x7D, 0x98))

        assert weather.wind_speed == 469237.76
        assert weather._wind_speed.unit_of_measurement == "m/s"
        assert weather._wind_speed.ha_device_class is None

    def test_wind_bearing(self):
        """Test wind bearing received."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather", xknx=xknx, group_address_brightness_east="1/3/8"
        )

        weather._wind_bearing.value = DPTArray((0xBF,))

        assert weather.wind_bearing == 270
        assert weather._wind_bearing.unit_of_measurement == "°"
        assert weather._wind_bearing.ha_device_class is None

    def test_state_lightning(self):
        """Test current_state returns lightning if wind alarm and rain alarm are true."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_rain_alarm="1/3/8",
            group_address_wind_alarm="1/3/9",
        )

        weather._rain_alarm.value = DPTBinary(1)
        weather._wind_alarm.value = DPTBinary(1)

        assert weather.ha_current_state() == WeatherCondition.LIGHTNING_RAINY

    def test_state_snowy_rainy(self):
        """Test snow rain if frost alarm and rain alarm are true."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_rain_alarm="1/3/8",
            group_address_frost_alarm="1/3/10",
        )

        weather._rain_alarm.value = DPTBinary(1)
        weather._frost_alarm.value = DPTBinary(1)

        assert weather.ha_current_state() == WeatherCondition.SNOWY_RAINY

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

        weather._wind_alarm.value = DPTBinary(1)

        assert weather.ha_current_state() == WeatherCondition.WINDY

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

        weather._rain_alarm.value = DPTBinary(1)

        assert weather.ha_current_state() == WeatherCondition.RAINY

    def test_cloudy_summer(self):
        """Test cloudy summer if illuminance matches defined interval."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
        )

        weather._brightness_south.value = DPTArray((0x46, 0x45))

        summer_date = datetime.datetime(2020, 10, 5, 18, 00)

        assert (
            weather.ha_current_state(current_date=summer_date)
            == WeatherCondition.CLOUDY
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

        weather._brightness_south.value = DPTArray((0x7C, 0x5C))

        summer_date = datetime.datetime(2020, 10, 5, 18, 00)

        assert (
            weather.ha_current_state(current_date=summer_date) == WeatherCondition.SUNNY
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

        weather._brightness_south.value = DPTArray((0x7C, 0x5C))

        winter_date = datetime.datetime(2020, 12, 5, 18, 00)

        assert (
            weather.ha_current_state(current_date=winter_date) == WeatherCondition.SUNNY
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

        weather._brightness_south.value = DPTArray((0x46, 0x45))

        winter_date = datetime.datetime(2020, 12, 31, 18, 00)

        assert (
            weather.ha_current_state(current_date=winter_date)
            == WeatherCondition.CLOUDY
        )

    def test_day_night(self):
        """Test day night mapping."""
        xknx = XKNX()
        weather: Weather = Weather(
            name="weather", xknx=xknx, group_address_day_night="1/3/20"
        )

        weather._day_night.value = DPTBinary(0)

        assert weather.ha_current_state() == WeatherCondition.CLEAR_NIGHT

    def test_weather_default(self):
        """Test default state mapping."""
        xknx = XKNX()
        weather: Weather = Weather(name="weather", xknx=xknx)

        assert weather.ha_current_state() == WeatherCondition.EXCEPTIONAL

    #
    # Create sensor tests
    #
    def test_create_sensor(self):
        """Test default state mapping."""
        xknx = XKNX()
        Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
        )

        assert len(xknx.devices) == 1

        Weather(
            name="weather",
            xknx=xknx,
            group_address_brightness_east="1/3/5",
            group_address_brightness_south="1/3/6",
            group_address_brightness_west="1/3/7",
            group_address_wind_alarm="1/5/4",
            create_sensors=True,
        )

        assert len(xknx.devices) == 6

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
        assert weather.has_group_address(GroupAddress("1/3/4"))
        assert weather.has_group_address(GroupAddress("7/7/0"))
        assert weather.has_group_address(GroupAddress("1/4/5"))
        assert not weather.has_group_address(GroupAddress("1/2/4"))

    #
    # HAS GROUP ADDRESS
    #
    def test_has_group_address(self):
        """Test sensor has group address."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_temperature="1/3/4")
        assert weather._temperature.has_group_address(GroupAddress("1/3/4"))
        assert not weather._temperature.has_group_address(GroupAddress("1/2/4"))

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        weather = Weather(name="weather", xknx=xknx, group_address_temperature="1/3/4")
        assert weather.unique_id == "1/3/4"
