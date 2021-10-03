"""Support for KNX/IP weather station."""
from __future__ import annotations

from xknx import XKNX
from xknx.devices import Weather as XknxWeather

from homeassistant.components.weather import WeatherEntity
from homeassistant.const import CONF_NAME, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .knx_entity import KnxEntity
from .schema import WeatherSchema


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up weather entities for KNX platform."""
    if not discovery_info or not discovery_info["platform_config"]:
        return
    platform_config = discovery_info["platform_config"]
    xknx: XKNX = hass.data[DOMAIN].xknx

    async_add_entities(
        KNXWeather(xknx, entity_config) for entity_config in platform_config
    )


def _create_weather(xknx: XKNX, config: ConfigType) -> XknxWeather:
    """Return a KNX weather device to be used within XKNX."""
    return XknxWeather(
        xknx,
        name=config[CONF_NAME],
        sync_state=config[WeatherSchema.CONF_SYNC_STATE],
        group_address_temperature=config[WeatherSchema.CONF_XKNX_TEMPERATURE_ADDRESS],
        group_address_brightness_south=config.get(
            WeatherSchema.CONF_XKNX_BRIGHTNESS_SOUTH_ADDRESS
        ),
        group_address_brightness_east=config.get(
            WeatherSchema.CONF_XKNX_BRIGHTNESS_EAST_ADDRESS
        ),
        group_address_brightness_west=config.get(
            WeatherSchema.CONF_XKNX_BRIGHTNESS_WEST_ADDRESS
        ),
        group_address_brightness_north=config.get(
            WeatherSchema.CONF_XKNX_BRIGHTNESS_NORTH_ADDRESS
        ),
        group_address_wind_speed=config.get(WeatherSchema.CONF_XKNX_WIND_SPEED_ADDRESS),
        group_address_wind_bearing=config.get(
            WeatherSchema.CONF_XKNX_WIND_BEARING_ADDRESS
        ),
        group_address_rain_alarm=config.get(WeatherSchema.CONF_XKNX_RAIN_ALARM_ADDRESS),
        group_address_frost_alarm=config.get(
            WeatherSchema.CONF_XKNX_FROST_ALARM_ADDRESS
        ),
        group_address_wind_alarm=config.get(WeatherSchema.CONF_XKNX_WIND_ALARM_ADDRESS),
        group_address_day_night=config.get(WeatherSchema.CONF_XKNX_DAY_NIGHT_ADDRESS),
        group_address_air_pressure=config.get(
            WeatherSchema.CONF_XKNX_AIR_PRESSURE_ADDRESS
        ),
        group_address_humidity=config.get(WeatherSchema.CONF_XKNX_HUMIDITY_ADDRESS),
    )


class KNXWeather(KnxEntity, WeatherEntity):
    """Representation of a KNX weather device."""

    _device: XknxWeather
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, xknx: XKNX, config: ConfigType) -> None:
        """Initialize of a KNX sensor."""
        super().__init__(_create_weather(xknx, config))
        self._attr_unique_id = str(self._device._temperature.group_address_state)

    @property
    def temperature(self) -> float | None:
        """Return current temperature."""
        return self._device.temperature

    @property
    def pressure(self) -> float | None:
        """Return current air pressure."""
        # KNX returns pA - HA requires hPa
        return (
            self._device.air_pressure / 100
            if self._device.air_pressure is not None
            else None
        )

    @property
    def condition(self) -> str:
        """Return current weather condition."""
        return self._device.ha_current_state().value

    @property
    def humidity(self) -> float | None:
        """Return current humidity."""
        return self._device.humidity

    @property
    def wind_bearing(self) -> int | None:
        """Return current wind bearing in degrees."""
        return self._device.wind_bearing

    @property
    def wind_speed(self) -> float | None:
        """Return current wind speed in km/h."""
        # KNX only supports wind speed in m/s
        return (
            self._device.wind_speed * 3.6
            if self._device.wind_speed is not None
            else None
        )
