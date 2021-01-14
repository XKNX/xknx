"""
Module for managing a weather station via KNX.

It provides functionality for

* reading current outside temperature
* reading current brightness in 3 directions (DPT 9.004)
* reading current alarms (DPTBinary)
* reading current wind speed in m/s (DPT 9.005)
* reading current air pressure (DPT 9.006)
* reading current humidity (DPT 9.007)

"""
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Iterator, Optional, Tuple

from xknx.remote_value import RemoteValue, RemoteValueSensor, RemoteValueSwitch

from . import BinarySensor, Sensor
from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX


class WeatherCondition(Enum):
    """Home assistant weather conditions (partially)."""

    clear_night = "clear-night"
    cloudy = "cloudy"
    lightning = "lightning"
    lightning_rainy = "lightning-rainy"
    partly_cloudy = "partly-cloudy"
    pouring = "pouring"
    rainy = "rainy"
    snowy = "snowy"
    snowy_rainy = "snowy-rainy"
    sunny = "sunny"
    windy = "windy"
    windy_variant = "windy_variant"
    exceptional = "exceptional"


class Season(Enum):
    """Seasonal mapping for illuminance."""

    winter = 0
    summer = 1


YEAR = 2000  # dummy leap year to allow input X-02-29 (leap day)
# Map year to winter and summer in order to be able to have seasonal illuminance checks
# Sun during summer is stronger than in winter
SEASONS = [
    (Season.winter, (date(YEAR, 1, 1), date(YEAR, 4, 20))),
    (Season.summer, (date(YEAR, 4, 21), date(YEAR, 10, 1))),
    (Season.winter, (date(YEAR, 10, 2), date(YEAR, 12, 31))),
]

# Define current condition
ILLUMINANCE_MAPPING: Tuple[
    Tuple[Season, Callable[[float], bool], WeatherCondition], ...
] = (
    (Season.summer, lambda lx: 2000 <= lx <= 20000, WeatherCondition.cloudy),
    (Season.summer, lambda lx: lx > 20000, WeatherCondition.sunny),
    (Season.winter, lambda lx: 999 <= lx <= 4500, WeatherCondition.cloudy),
    (Season.winter, lambda lx: lx > 4500, WeatherCondition.sunny),
)


# pylint: disable=too-many-public-methods, too-many-instance-attributes
class Weather(Device):
    """Class for managing a weather device."""

    # pylint: disable=too-many-locals
    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address_temperature: Optional["GroupAddressableType"] = None,
        group_address_brightness_south: Optional["GroupAddressableType"] = None,
        group_address_brightness_north: Optional["GroupAddressableType"] = None,
        group_address_brightness_west: Optional["GroupAddressableType"] = None,
        group_address_brightness_east: Optional["GroupAddressableType"] = None,
        group_address_wind_speed: Optional["GroupAddressableType"] = None,
        group_address_rain_alarm: Optional["GroupAddressableType"] = None,
        group_address_frost_alarm: Optional["GroupAddressableType"] = None,
        group_address_wind_alarm: Optional["GroupAddressableType"] = None,
        group_address_day_night: Optional["GroupAddressableType"] = None,
        group_address_air_pressure: Optional["GroupAddressableType"] = None,
        group_address_humidity: Optional["GroupAddressableType"] = None,
        expose_sensors: bool = False,
        sync_state: bool = True,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ) -> None:
        """Initialize Weather class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self._temperature = RemoteValueSensor(
            xknx,
            group_address_state=group_address_temperature,
            sync_state=sync_state,
            value_type="temperature",
            device_name=self.name,
            feature_name="Temperature",
            after_update_cb=self.after_update,
        )

        self._brightness_south = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_south,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness south",
            after_update_cb=self.after_update,
        )

        self._brightness_north = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_north,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness north",
            after_update_cb=self.after_update,
        )

        self._brightness_west = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_west,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness west",
            after_update_cb=self.after_update,
        )

        self._brightness_east = RemoteValueSensor(
            xknx,
            group_address_state=group_address_brightness_east,
            sync_state=sync_state,
            value_type="illuminance",
            device_name=self.name,
            feature_name="Brightness east",
            after_update_cb=self.after_update,
        )

        self._wind_speed = RemoteValueSensor(
            xknx,
            group_address_state=group_address_wind_speed,
            sync_state=sync_state,
            value_type="wind_speed_ms",
            device_name=self.name,
            feature_name="Wind speed",
            after_update_cb=self.after_update,
        )

        self._rain_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_rain_alarm,
            device_name=self.name,
            feature_name="Rain alarm",
            after_update_cb=self.after_update,
        )

        self._frost_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_frost_alarm,
            device_name=self.name,
            feature_name="Frost alarm",
            after_update_cb=self.after_update,
        )

        self._wind_alarm = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_wind_alarm,
            device_name=self.name,
            feature_name="Wind alarm",
            after_update_cb=self.after_update,
        )

        self._day_night = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_day_night,
            device_name=self.name,
            feature_name="Day/Night",
            after_update_cb=self.after_update,
        )

        self._air_pressure = RemoteValueSensor(
            xknx,
            group_address_state=group_address_air_pressure,
            sync_state=sync_state,
            value_type="pressure_2byte",
            device_name=self.name,
            feature_name="Air pressure",
            after_update_cb=self.after_update,
        )

        self._humidity = RemoteValueSensor(
            xknx,
            group_address_state=group_address_humidity,
            sync_state=sync_state,
            value_type="humidity",
            device_name=self.name,
            feature_name="Humidity",
            after_update_cb=self.after_update,
        )

        if expose_sensors:
            self.expose_sensors()

    def _iter_remote_values(self) -> Iterator[RemoteValue]:
        """Iterate the devices remote values."""
        yield from [
            self._temperature,
            self._brightness_south,
            self._brightness_north,
            self._brightness_east,
            self._brightness_west,
            self._wind_speed,
            self._rain_alarm,
            self._wind_alarm,
            self._frost_alarm,
            self._day_night,
            self._air_pressure,
            self._humidity,
        ]

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)

    @property
    def temperature(self) -> Optional[float]:
        """Return current temperature."""
        return self._temperature.value  # type: ignore

    @property
    def brightness_south(self) -> float:
        """Return brightness south."""
        return (  # type: ignore
            0.0
            if self._brightness_south.value is None
            else self._brightness_south.value
        )

    @property
    def brightness_north(self) -> float:
        """Return brightness north."""
        return (  # type: ignore
            0.0
            if self._brightness_north.value is None
            else self._brightness_north.value
        )

    @property
    def brightness_east(self) -> float:
        """Return brightness east."""
        return (  # type: ignore
            0.0 if self._brightness_east.value is None else self._brightness_east.value
        )

    @property
    def brightness_west(self) -> float:
        """Return brightness west."""
        return (  # type: ignore
            0.0 if self._brightness_west.value is None else self._brightness_west.value
        )

    @property
    def wind_speed(self) -> Optional[float]:
        """Return wind speed in m/s."""
        return self._wind_speed.value  # type: ignore

    @property
    def rain_alarm(self) -> Optional[bool]:
        """Return True if rain alarm False if not."""
        return self._rain_alarm.value  # type: ignore

    @property
    def wind_alarm(self) -> Optional[bool]:
        """Return True if wind alarm False if not."""
        return self._wind_alarm.value  # type: ignore

    @property
    def frost_alarm(self) -> Optional[bool]:
        """Return True if frost alarm False if not."""
        return self._frost_alarm.value  # type: ignore

    @property
    def day_night(self) -> Optional[bool]:
        """Return day or night."""
        return self._day_night.value  # type: ignore

    @property
    def air_pressure(self) -> Optional[float]:
        """Return pressure in Pa."""
        return self._air_pressure.value  # type: ignore

    @property
    def humidity(self) -> Optional[float]:
        """Return humidity in %."""
        return self._humidity.value  # type: ignore

    @property
    def max_brightness(self) -> float:
        """Return highest illuminance from all sensors."""
        return max(
            self.brightness_west,
            self.brightness_south,
            self.brightness_north,
            self.brightness_east,
        )

    def expose_sensors(self) -> None:
        """Expose sensors to xknx."""
        for suffix, group_address in (
            ("_rain_alarm", self._rain_alarm.group_address_state),
            ("_wind_alarm", self._wind_alarm.group_address_state),
            ("_frost_alarm", self._frost_alarm.group_address_state),
            ("_day_night", self._day_night.group_address_state),
        ):
            if group_address is not None:
                BinarySensor(
                    self.xknx,
                    name=self.name + suffix,
                    group_address_state=group_address,
                )

        for suffix, group_address, value_type in (
            (
                "_temperature",
                self._temperature.group_address_state,
                "temperature",
            ),
            (
                "_brightness_south",
                self._brightness_south.group_address_state,
                "illuminance",
            ),
            (
                "_brightness_north",
                self._brightness_north.group_address_state,
                "illuminance",
            ),
            (
                "_brightness_west",
                self._brightness_west.group_address_state,
                "illuminance",
            ),
            (
                "_brightness_east",
                self._brightness_east.group_address_state,
                "illuminance",
            ),
            (
                "_wind_speed",
                self._wind_speed.group_address_state,
                "wind_speed_ms",
            ),
            (
                "_air_pressure",
                self._air_pressure.group_address_state,
                "pressure",
            ),
            (
                "_humidity",
                self._humidity.group_address_state,
                "humidity",
            ),
        ):
            if group_address is not None:
                Sensor(
                    self.xknx,
                    name=self.name + suffix,
                    group_address_state=group_address,
                    value_type=value_type,
                )

    # pylint: disable=too-many-return-statements
    def ha_current_state(self, current_date: date = date.today()) -> WeatherCondition:
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
            return WeatherCondition.lightning_rainy

        if self.frost_alarm and self.rain_alarm:
            return WeatherCondition.snowy_rainy

        if self.rain_alarm:
            return WeatherCondition.rainy

        if self.wind_alarm:
            return WeatherCondition.windy

        current_season: Season = _get_season(current_date)
        _season: Season
        function: Callable[[float], bool]
        result: WeatherCondition
        for _season, function, result in ILLUMINANCE_MAPPING:
            if _season == current_season and function(self.max_brightness):
                return result

        if self.day_night is False:
            return WeatherCondition.clear_night

        return WeatherCondition.exceptional

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Any) -> "Weather":
        """Initialize object from configuration structure."""
        group_address_temperature = config.get("group_address_temperature")
        group_address_brightness_south = config.get("group_address_brightness_south")
        group_address_brightness_north = config.get("group_address_brightness_north")
        group_address_brightness_west = config.get("group_address_brightness_west")
        group_address_brightness_east = config.get("group_address_brightness_east")
        group_address_wind_speed = config.get("group_address_wind_speed")
        group_address_rain_alarm = config.get("group_address_rain_alarm")
        group_address_frost_alarm = config.get("group_address_frost_alarm")
        group_address_wind_alarm = config.get("group_address_wind_alarm")
        group_address_day_night = config.get("group_address_day_night")
        group_address_air_pressure = config.get("group_address_air_pressure")
        group_address_humidity = config.get("group_address_humidity")
        expose_sensors = config.get("expose_sensors", False)
        sync_state = config.get("sync_state", True)

        return cls(
            xknx,
            name,
            group_address_temperature=group_address_temperature,
            group_address_brightness_south=group_address_brightness_south,
            group_address_brightness_north=group_address_brightness_north,
            group_address_brightness_west=group_address_brightness_west,
            group_address_brightness_east=group_address_brightness_east,
            group_address_wind_speed=group_address_wind_speed,
            group_address_rain_alarm=group_address_rain_alarm,
            group_address_frost_alarm=group_address_frost_alarm,
            group_address_wind_alarm=group_address_wind_alarm,
            group_address_day_night=group_address_day_night,
            group_address_air_pressure=group_address_air_pressure,
            group_address_humidity=group_address_humidity,
            expose_sensors=expose_sensors,
            sync_state=sync_state,
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<Weather name="{}" '
            'temperature="{}" brightness_south="{}" brightness_north="{}" brightness_west="{}" '
            'brightness_east="{}" wind_speed="{}" rain_alarm="{}" '
            'wind_alarm="{}" frost_alarm="{}" day_night="{}" '
            'air_pressure="{}" humidity="{}" />'.format(
                self.name,
                self._temperature.group_addr_str(),
                self._brightness_south.group_addr_str(),
                self._brightness_north.group_addr_str(),
                self._brightness_west.group_addr_str(),
                self._brightness_east.group_addr_str(),
                self._wind_speed.group_addr_str(),
                self._rain_alarm.group_addr_str(),
                self._wind_alarm.group_addr_str(),
                self._frost_alarm.group_addr_str(),
                self._day_night.group_addr_str(),
                self._air_pressure.group_addr_str(),
                self._humidity.group_addr_str(),
            )
        )
