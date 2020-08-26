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
from typing import Optional, Generator, Union, Any

from xknx.remote_value import RemoteValueSensor, RemoteValueSwitch, RemoteValue

from .device import Device


class Weather(Device):
    """Class for managing a weather device."""

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
                 device_updated_cb=None):
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

    def _iter_remote_values(self):
        """Iterate the devices remote values."""
        yield self._temperature
        yield self._brightness_south
        yield self._brightness_east
        yield self._brightness_west
        yield self._wind_speed
        yield self._rain_alarm
        yield self._wind_alarm
        yield self._frost_alarm
        yield self._day_night
        yield self._air_pressure
        yield self._humidity

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self._temperature.process(telegram)
        await self._brightness_south.process(telegram)
        await self._brightness_west.process(telegram)
        await self._brightness_east.process(telegram)
        await self._wind_speed.process(telegram)
        await self._rain_alarm.process(telegram)
        await self._wind_alarm.process(telegram)
        await self._frost_alarm.process(telegram)
        await self._day_night.process(telegram)
        await self._air_pressure.process(telegram)
        await self._humidity.process(telegram)

    @property
    def temperature(self) -> float:
        """Return current temperature."""
        return self._temperature.value

    @property
    def brightness_south(self):
        """Return brightness south"""
        return self._brightness_south.value

    @property
    def brightness_east(self):
        """Return brightness east"""
        return self._brightness_east.value

    @property
    def brightness_west(self):
        """Return brightness west"""
        return self._brightness_west.value

    @property
    def wind_speed(self):
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
    def humidity(self):
        """Return humidity in %"""
        return self._humidity.value

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

    def __eq__(self, other) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
