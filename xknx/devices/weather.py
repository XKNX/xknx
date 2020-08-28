"""
Module for managing a weather station via KNX.

It provides functionality for

* reading current outside temperature
* reading current brightness in 3 directions
* reading current alarms
* reading current wind speed in m/s (DPT 9.005)
* reading current air pressure (DPT 9.006)
* reading current humidity (DPT 9.007)

"""
from datetime import date, datetime
from enum import Enum
from typing import Optional, Callable, Generator

from xknx.remote_value import RemoteValueSensor, RemoteValueSwitch, RemoteValue
from .device import Device


class WeatherCondition(Enum):
    """Home assistant weather conditions (partially)."""
    clear_night = 'clear-night'
    cloudy = 'cloudy'
    lightning = 'lightning'
    lightning_rainy = 'lightning-rainy'
    partly_cloudy = 'partly-cloudy'
    pouring = 'pouring'
    rainy = 'rainy'
    snowy = 'snowy'
    snowy_rainy = 'snowy-rainy'
    sunny = 'sunny'
    windy = 'windy'
    windy_variant = 'windy_variant'
    exceptional = 'exceptional'


class Season(Enum):
    """Seasonal mapping for illuminance."""
    winter = 0
    summer = 1


YEAR = 2000  # dummy leap year to allow input X-02-29 (leap day)
# Map year to winter and summer in order to be able to have seasonal illuminance checks
# Sun during summer is stronger than in winter
seasons = [(Season.winter, (date(YEAR, 1, 1), date(YEAR, 4, 20))),
           (Season.summer, (date(YEAR, 4, 21), date(YEAR, 10, 20))),
           (Season.winter, (date(YEAR, 10, 21), date(YEAR, 12, 31)))]


def get_season(now):
    """Return winter or summer."""
    if isinstance(now, datetime):
        now = now.date()
    now = now.replace(year=YEAR)
    return next(season for season, (start, end) in seasons
                if start <= now <= end)


# Define current condition
ILLUMINANCE_MAPPING = (
    (Season.summer, lambda lx: 7500 <= lx <= 20000, WeatherCondition.cloudy),
    (Season.summer, lambda lx: lx > 20000, WeatherCondition.sunny),
    (Season.winter, lambda lx: 1500 <= lx <= 4500, WeatherCondition.cloudy),
    (Season.winter, lambda lx: lx > 4500, WeatherCondition.sunny),
)


# pylint: disable=too-many-public-methods, too-many-instance-attributes
class Weather(Device):
    """Class for managing a weather device."""

    # pylint: disable=too-many-locals
    def __init__(self,
                 xknx,
                 name: str,
                 group_address_temperature: str = None,
                 group_address_brightness_south: Optional[str] = None,
                 group_address_brightness_west: Optional[str] = None,
                 group_address_brightness_east: Optional[str] = None,
                 group_address_wind_speed: Optional[str] = None,
                 group_address_rain_alarm: Optional[str] = None,
                 group_address_frost_alarm: Optional[str] = None,
                 group_address_wind_alarm: Optional[str] = None,
                 group_address_day_night: Optional[str] = None,
                 group_address_air_pressure: Optional[str] = None,
                 group_address_humidity: Optional[str] = None,
                 expose_sensors: bool = True,
                 sync_state: bool = True,
                 device_updated_cb=None) -> None:
        """Initialize Weather class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self._temperature = RemoteValueSensor(
            xknx,
            group_address_state=group_address_temperature,
            sync_state=sync_state,
            value_type="temperature",
            device_name=self.name,
            after_update_cb=self.after_update)

        self._brightness_south = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_south,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            after_update_cb=self.after_update)

        self._brightness_west = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_west,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            after_update_cb=self.after_update)

        self._brightness_east = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_east,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            after_update_cb=self.after_update)

        self._wind_speed = RemoteValueSensor(
            xknx,
            group_address_state=group_address_wind_speed,
            sync_state=sync_state,
            value_type="wind_speed_ms",
            device_name=self.name,
            after_update_cb=self.after_update)

        self._rain_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_rain_alarm,
            device_name=self.name,
            feature_name="State",
            after_update_cb=self.after_update)

        self._frost_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_frost_alarm,
            device_name=self.name,
            feature_name="State",
            after_update_cb=self.after_update)

        self._wind_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_wind_alarm,
            device_name=self.name,
            feature_name="State",
            after_update_cb=self.after_update)

        self._day_night = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_day_night,
            device_name=self.name,
            feature_name="State",
            after_update_cb=self.after_update)

        self._air_pressure = RemoteValueSensor(
            xknx,
            group_address_state=group_address_air_pressure,
            sync_state=sync_state,
            value_type="pressure",
            device_name=self.name,
            after_update_cb=self.after_update)

        self._humidity = RemoteValueSensor(
            xknx,
            group_address_state=group_address_humidity,
            sync_state=sync_state,
            value_type="humidity",
            device_name=self.name,
            after_update_cb=self.after_update)

    def _iter_remote_values(self) -> Generator[RemoteValue, None, None]:
        """Iterate the devices remote values."""
        yield from [self._temperature, self._brightness_south, self._brightness_east, self._brightness_west,
                    self._wind_speed, self._rain_alarm, self._rain_alarm, self._wind_alarm, self._frost_alarm,
                    self._day_night, self._air_pressure, self._humidity]

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)

    @property
    def temperature(self) -> float:
        """Return current temperature."""
        return self._temperature.value

    @property
    def brightness_south(self) -> float:
        """Return brightness south"""
        return 0.0 if self._brightness_south.value is None else self._brightness_south.value

    @property
    def brightness_east(self) -> float:
        """Return brightness east"""
        return 0.0 if self._brightness_east.value is None else self._brightness_east.value

    @property
    def brightness_west(self) -> float:
        """Return brightness west"""
        return 0.0 if self._brightness_west.value is None else self._brightness_west.value

    @property
    def wind_speed(self) -> Optional[float]:
        """Return wind speed in m/s"""
        return self._wind_speed.value

    @property
    def rain_alarm(self) -> Optional[bool]:
        """Return True if rain alarm False if not"""
        return self._rain_alarm.value

    @property
    def wind_alarm(self) -> Optional[bool]:
        """Return True if wind alarm False if not"""
        return self._wind_alarm.value

    @property
    def frost_alarm(self) -> Optional[bool]:
        """Return True if frost alarm False if not"""
        return self._frost_alarm.value

    @property
    def day_night(self) -> Optional[bool]:
        """Return day or night"""
        return self._day_night.value

    @property
    def air_pressure(self):
        """Return pressure in Pa"""
        return self._air_pressure.value

    @property
    def humidity(self) -> Optional[float]:
        """Return humidity in %"""
        return self._humidity.value

    @property
    def max_brightness(self) -> float:
        """Return highest illuminance from all sensors."""
        return max(self.brightness_west, self.brightness_south, self.brightness_east)

    @property
    def ha_current_state(self, current_date=date.today()) -> WeatherCondition:
        """Return the current state for home assistant."""
        if self.wind_alarm and self.rain_alarm:
            return WeatherCondition.lightning_rainy

        if self.frost_alarm and self.rain_alarm:
            return WeatherCondition.snowy_rainy

        if self.rain_alarm:
            return WeatherCondition.rainy

        if self.wind_alarm:
            return WeatherCondition.windy

        current_season: Season = get_season(current_date)
        season: Season
        function: Callable[[float], bool]
        result: WeatherCondition
        for season, function, result in ILLUMINANCE_MAPPING:
            if season == current_season and function(self.max_brightness):
                return result

        if self.day_night is False:
            return WeatherCondition.clear_night

        return WeatherCondition.exceptional

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<Weather name="{0}" ' \
               'temperature="{1}" brightness_south="{2}" brightness_west="{3}" ' \
               'brightness_east="{4}" wind_speed="{5}" rain_alarm="{6}" ' \
               'wind_alarm="{7}" frost_alarm="{8}" day_night="{9}" ' \
               'air_pressure="{10}" humidity="{11}" />' \
            .format(self.name,
                    self.temperature,
                    self.brightness_south,
                    self.brightness_west,
                    self.brightness_east,
                    self.wind_speed,
                    self.rain_alarm,
                    self.wind_alarm,
                    self.frost_alarm,
                    self.day_night,
                    self.air_pressure,
                    self.humidity)
