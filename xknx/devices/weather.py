"""
Module for managing a weather station via KNX.

It provides functionality for

* reading current outside temperature
* reading current brightness in 3 directions (DPT 9.004)
* reading current alarms (DPTBinary)
* reading current wind speed in m/s (DPT 9.005)
* reading current wind bearing in degrees (DPT 5.003)
* reading current air pressure (DPT 9.006)
* reading current humidity (DPT 9.007)

"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueNumeric,
    RemoteValueSwitch,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class WeatherCondition(Enum):
    """Home assistant weather conditions (partially)."""

    CLEAR_NIGHT = "clear-night"
    CLOUDY = "cloudy"
    LIGHTNING = "lightning"
    LIGHTNING_RAINY = "lightning-rainy"
    PARTLY_CLOUDY = "partly-cloudy"
    POURING = "pouring"
    RAINY = "rainy"
    SNOWY = "snowy"
    SNOWY_RAINY = "snowy-rainy"
    SUNNY = "sunny"
    WINDY = "windy"
    WINDY_VARIANT = "windy_variant"
    EXCEPTIONAL = "exceptional"


class Season(Enum):
    """Seasonal mapping for illuminance."""

    WINTER = 0
    SUMMER = 1


YEAR = 2000  # dummy leap year to allow input X-02-29 (leap day)
# Map year to winter and summer in order to be able to have seasonal illuminance checks
# Sun during summer is stronger than in winter
SEASONS = [
    (Season.WINTER, (date(YEAR, 1, 1), date(YEAR, 4, 20))),
    (Season.SUMMER, (date(YEAR, 4, 21), date(YEAR, 10, 1))),
    (Season.WINTER, (date(YEAR, 10, 2), date(YEAR, 12, 31))),
]

# Define current condition
ILLUMINANCE_MAPPING: tuple[
    tuple[Season, Callable[[float], bool], WeatherCondition], ...
] = (
    (Season.SUMMER, lambda lx: 2000 <= lx <= 20000, WeatherCondition.CLOUDY),
    (Season.SUMMER, lambda lx: lx > 20000, WeatherCondition.SUNNY),
    (Season.WINTER, lambda lx: 999 <= lx <= 4500, WeatherCondition.CLOUDY),
    (Season.WINTER, lambda lx: lx > 4500, WeatherCondition.SUNNY),
)


class Weather(Device):
    """Class for managing a weather device."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_temperature: GroupAddressesType | None = None,
        group_address_brightness_south: GroupAddressesType | None = None,
        group_address_brightness_north: GroupAddressesType | None = None,
        group_address_brightness_west: GroupAddressesType | None = None,
        group_address_brightness_east: GroupAddressesType | None = None,
        group_address_wind_speed: GroupAddressesType | None = None,
        group_address_wind_bearing: GroupAddressesType | None = None,
        group_address_rain_alarm: GroupAddressesType | None = None,
        group_address_frost_alarm: GroupAddressesType | None = None,
        group_address_wind_alarm: GroupAddressesType | None = None,
        group_address_day_night: GroupAddressesType | None = None,
        group_address_air_pressure: GroupAddressesType | None = None,
        group_address_humidity: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_updated_cb: DeviceCallbackType[Weather] | None = None,
    ) -> None:
        """Initialize Weather class."""
        super().__init__(xknx, name, device_updated_cb)

        self._temperature = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_temperature,
            sync_state=sync_state,
            value_type="temperature",
            device_name=self.name,
            feature_name="Temperature",
            after_update_cb=self.after_update,
        )

        self._brightness_south = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_brightness_south,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness south",
            after_update_cb=self.after_update,
        )

        self._brightness_north = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_brightness_north,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness north",
            after_update_cb=self.after_update,
        )

        self._brightness_west = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_brightness_west,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness west",
            after_update_cb=self.after_update,
        )

        self._brightness_east = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_brightness_east,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness east",
            after_update_cb=self.after_update,
        )

        self._wind_speed = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_wind_speed,
            sync_state=sync_state,
            value_type="wind_speed_ms",
            device_name=self.name,
            feature_name="Wind speed",
            after_update_cb=self.after_update,
        )

        self._wind_bearing = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_wind_bearing,
            sync_state=sync_state,
            value_type="angle",
            device_name=self.name,
            feature_name="Wind bearing",
            after_update_cb=self.after_update,
        )

        self._rain_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_rain_alarm,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Rain alarm",
            after_update_cb=self.after_update,
        )

        self._frost_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_frost_alarm,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Frost alarm",
            after_update_cb=self.after_update,
        )

        self._wind_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_wind_alarm,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Wind alarm",
            after_update_cb=self.after_update,
        )

        self._day_night = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_day_night,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Day/Night",
            after_update_cb=self.after_update,
        )

        self._air_pressure = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_air_pressure,
            sync_state=sync_state,
            value_type="pressure_2byte",
            device_name=self.name,
            feature_name="Air pressure",
            after_update_cb=self.after_update,
        )

        self._humidity = RemoteValueNumeric(
            xknx,
            group_address_state=group_address_humidity,
            sync_state=sync_state,
            value_type="humidity",
            device_name=self.name,
            feature_name="Humidity",
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices remote values."""
        yield self._temperature
        yield self._brightness_south
        yield self._brightness_north
        yield self._brightness_east
        yield self._brightness_west
        yield self._wind_speed
        yield self._wind_bearing
        yield self._rain_alarm
        yield self._wind_alarm
        yield self._frost_alarm
        yield self._day_night
        yield self._air_pressure
        yield self._humidity

    async def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)

    @property
    def temperature(self) -> float | None:
        """Return current temperature."""
        return self._temperature.value

    @property
    def brightness_south(self) -> float:
        """Return brightness south."""
        if self._brightness_south.value is not None:
            return self._brightness_south.value
        return 0.0

    @property
    def brightness_north(self) -> float:
        """Return brightness north."""
        if self._brightness_north.value is not None:
            return self._brightness_north.value
        return 0.0

    @property
    def brightness_east(self) -> float:
        """Return brightness east."""
        if self._brightness_east.value is not None:
            return self._brightness_east.value
        return 0.0

    @property
    def brightness_west(self) -> float:
        """Return brightness west."""
        if self._brightness_west.value is not None:
            return self._brightness_west.value
        return 0.0

    @property
    def wind_speed(self) -> float | None:
        """Return wind speed in m/s."""
        return self._wind_speed.value

    @property
    def wind_bearing(self) -> int | None:
        """Return wind bearing in °."""
        return self._wind_bearing.value  # type: ignore

    @property
    def rain_alarm(self) -> bool | None:
        """Return True if rain alarm False if not."""
        return self._rain_alarm.value

    @property
    def wind_alarm(self) -> bool | None:
        """Return True if wind alarm False if not."""
        return self._wind_alarm.value

    @property
    def frost_alarm(self) -> bool | None:
        """Return True if frost alarm False if not."""
        return self._frost_alarm.value

    @property
    def day_night(self) -> bool | None:
        """Return day or night."""
        return self._day_night.value

    @property
    def air_pressure(self) -> float | None:
        """Return pressure in Pa."""
        return self._air_pressure.value

    @property
    def humidity(self) -> float | None:
        """Return humidity in %."""
        return self._humidity.value

    @property
    def max_brightness(self) -> float:
        """Return highest illuminance from all sensors."""
        return max(
            self.brightness_west,
            self.brightness_south,
            self.brightness_north,
            self.brightness_east,
        )

    def ha_current_state(self, current_date: date | None = None) -> WeatherCondition:
        """Return the current state for home assistant."""

        def _get_season(now: date) -> Season:
            """Return winter or summer."""
            if isinstance(now, datetime):
                now = now.date()
            now = now.replace(year=YEAR)
            return next(
                season for season, (start, end) in SEASONS if start <= now <= end
            )

        if self.wind_alarm and self.rain_alarm:
            return WeatherCondition.LIGHTNING_RAINY

        if self.frost_alarm and self.rain_alarm:
            return WeatherCondition.SNOWY_RAINY

        if self.rain_alarm:
            return WeatherCondition.RAINY

        if self.wind_alarm:
            return WeatherCondition.WINDY

        _current_date = current_date if current_date is not None else date.today()
        current_season: Season = _get_season(_current_date)
        _season: Season
        function: Callable[[float], bool]
        result: WeatherCondition
        for _season, function, result in ILLUMINANCE_MAPPING:
            if _season == current_season and function(self.max_brightness):
                return result

        if self.day_night is False:
            return WeatherCondition.CLEAR_NIGHT

        return WeatherCondition.EXCEPTIONAL

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Weather name="{self.name}" '
            f"temperature={self._temperature.group_addr_str()} "
            f"brightness_south={self._brightness_south.group_addr_str()} "
            f"brightness_north={self._brightness_north.group_addr_str()} "
            f"brightness_west={self._brightness_west.group_addr_str()} "
            f"brightness_east={self._brightness_east.group_addr_str()} "
            f"wind_speed={self._wind_speed.group_addr_str()} "
            f"wind_bearing={self._wind_bearing.group_addr_str()} "
            f"rain_alarm={self._rain_alarm.group_addr_str()} "
            f"wind_alarm={self._wind_alarm.group_addr_str()} "
            f"frost_alarm={self._frost_alarm.group_addr_str()} "
            f"day_night={self._day_night.group_addr_str()} "
            f"air_pressure={self._air_pressure.group_addr_str()} "
            f"humidity={self._humidity.group_addr_str()} "
            "/>"
        )
