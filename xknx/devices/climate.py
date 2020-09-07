"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
from enum import Enum

from xknx.remote_value import (
    RemoteValueSetpointShift,
    RemoteValueSwitch,
    RemoteValueTemp,
)

from .climate_mode import ClimateMode
from .device import Device


class SetpointShiftMode(Enum):
    """Enum for setting the setpoint shift mode."""

    DPT6010 = 1
    DPT9002 = 2


DEFAULT_SETPOINT_SHIFT_MAX = 6
DEFAULT_SETPOINT_SHIFT_MIN = -6
DEFAULT_TEMPERATURE_STEP = 0.1
DEFAULT_SETPOINT_SHIFT_MODE = SetpointShiftMode.DPT6010


class Climate(Device):
    """Class for managing the climate."""

    # pylint: disable=too-many-instance-attributes,invalid-name
    def __init__(
        self,
        xknx,
        name,
        group_address_temperature=None,
        group_address_target_temperature=None,
        group_address_target_temperature_state=None,
        group_address_setpoint_shift=None,
        group_address_setpoint_shift_state=None,
        setpoint_shift_mode=DEFAULT_SETPOINT_SHIFT_MODE,
        setpoint_shift_max=DEFAULT_SETPOINT_SHIFT_MAX,
        setpoint_shift_min=DEFAULT_SETPOINT_SHIFT_MIN,
        temperature_step=DEFAULT_TEMPERATURE_STEP,
        group_address_on_off=None,
        group_address_on_off_state=None,
        on_off_invert=False,
        min_temp=None,
        max_temp=None,
        mode=None,
        device_updated_cb=None,
    ):
        """Initialize Climate class."""
        # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        super().__init__(xknx, name, device_updated_cb)

        self.min_temp = min_temp
        self.max_temp = max_temp
        self.setpoint_shift_min = setpoint_shift_min
        self.setpoint_shift_max = setpoint_shift_max
        self.temperature_step = temperature_step

        self.temperature = RemoteValueTemp(
            xknx,
            group_address_state=group_address_temperature,
            device_name=self.name,
            feature_name="Current Temperature",
            after_update_cb=self.after_update,
        )

        self.target_temperature = RemoteValueTemp(
            xknx,
            group_address_target_temperature,
            group_address_target_temperature_state,
            device_name=self.name,
            feature_name="Target temperature",
            after_update_cb=self.after_update,
        )

        if setpoint_shift_mode == SetpointShiftMode.DPT9002:
            self._setpoint_shift = RemoteValueTemp(
                xknx,
                group_address_setpoint_shift,
                group_address_setpoint_shift_state,
                device_name=self.name,
                after_update_cb=self.after_update,
            )
        else:
            self._setpoint_shift = RemoteValueSetpointShift(
                xknx,
                group_address_setpoint_shift,
                group_address_setpoint_shift_state,
                device_name=self.name,
                after_update_cb=self.after_update,
                setpoint_shift_step=self.temperature_step,
            )

        self.supports_on_off = (
            group_address_on_off is not None or group_address_on_off_state is not None
        )

        self.on = RemoteValueSwitch(
            xknx,
            group_address_on_off,
            group_address_on_off_state,
            device_name=self.name,
            after_update_cb=self.after_update,
            invert=on_off_invert,
        )

        self.mode = mode

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        yield from (
            self.temperature,
            self.target_temperature,
            self._setpoint_shift,
            self.on,
        )

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        # pylint: disable=too-many-locals
        group_address_temperature = config.get("group_address_temperature")
        group_address_target_temperature = config.get(
            "group_address_target_temperature"
        )
        group_address_target_temperature_state = config.get(
            "group_address_target_temperature_state"
        )
        group_address_setpoint_shift = config.get("group_address_setpoint_shift")
        group_address_setpoint_shift_state = config.get(
            "group_address_setpoint_shift_state"
        )
        setpoint_shift_mode = config.get(
            "setpoint_shift_mode", DEFAULT_SETPOINT_SHIFT_MODE
        )
        setpoint_shift_max = config.get(
            "setpoint_shift_max", DEFAULT_SETPOINT_SHIFT_MAX
        )
        setpoint_shift_min = config.get(
            "setpoint_shift_min", DEFAULT_SETPOINT_SHIFT_MIN
        )
        temperature_step = config.get("temperature_step", DEFAULT_TEMPERATURE_STEP)
        group_address_on_off = config.get("group_address_on_off")
        group_address_on_off_state = config.get("group_address_on_off_state")
        on_off_invert = config.get("on_off_invert", False)
        min_temp = config.get("min_temp")
        max_temp = config.get("max_temp")

        climate_mode = None
        if "mode" in config:
            climate_mode = ClimateMode.from_config(
                xknx=xknx, name=None, config=config["mode"]
            )

        return cls(
            xknx,
            name,
            group_address_temperature=group_address_temperature,
            group_address_target_temperature=group_address_target_temperature,
            group_address_target_temperature_state=group_address_target_temperature_state,
            group_address_setpoint_shift=group_address_setpoint_shift,
            group_address_setpoint_shift_state=group_address_setpoint_shift_state,
            setpoint_shift_mode=setpoint_shift_mode,
            setpoint_shift_max=setpoint_shift_max,
            setpoint_shift_min=setpoint_shift_min,
            temperature_step=temperature_step,
            group_address_on_off=group_address_on_off,
            group_address_on_off_state=group_address_on_off_state,
            on_off_invert=on_off_invert,
            min_temp=min_temp,
            max_temp=max_temp,
            mode=climate_mode,
        )

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        if self.mode is not None and self.mode.has_group_address(group_address):
            return True
        return super().has_group_address(group_address)

    @property
    def is_on(self):
        """Return power status."""
        # None will return False
        return bool(self.on.value)

    async def turn_on(self):
        """Set power status to on."""
        await self.on.on()

    async def turn_off(self):
        """Set power status to off."""
        await self.on.off()

    @property
    def initialized_for_setpoint_shift_calculations(self):
        """Test if object is initialized for setpoint shift calculations."""
        if not self._setpoint_shift.initialized:
            return False
        if self._setpoint_shift.value is None:
            return False
        if not self.target_temperature.initialized:
            return False
        if self.target_temperature.value is None:
            return False
        return True

    async def set_target_temperature(self, target_temperature):
        """Send new target temperature or setpoint_shift to KNX bus."""
        if self.initialized_for_setpoint_shift_calculations:
            temperature_delta = target_temperature - self.base_temperature
            await self.set_setpoint_shift(temperature_delta)
        else:
            validated_temp = self.validate_value(
                target_temperature, self.min_temp, self.max_temp
            )
            await self.target_temperature.set(validated_temp)

    @property
    def base_temperature(self):
        """
        Return the base temperature.

        Base temperature is the default temperature (setpoint-shift=0) for the active climate mode.
        As this value is usually not available via KNX, we have to derive this from the current
        target temperature and the current set point shift.
        """
        if self.initialized_for_setpoint_shift_calculations:
            return self.target_temperature.value - self.setpoint_shift
        return None

    @property
    def setpoint_shift(self):
        """Return current offset from base temperature in Kelvin."""
        return self._setpoint_shift.value

    def validate_value(self, value, min_value, max_value):
        """Check boundaries of temperature and return valid temperature value."""
        if (min_value is not None) and (value < min_value):
            self.xknx.logger.warning("Min value exceeded at %s: %s", self.name, value)
            return min_value
        if (max_value is not None) and (value > max_value):
            self.xknx.logger.warning("Max value exceeded at %s: %s", self.name, value)
            return max_value
        return value

    async def set_setpoint_shift(self, offset):
        """Send new temperature offset to KNX bus."""
        validated_offset = self.validate_value(
            offset, self.setpoint_shift_min, self.setpoint_shift_max
        )
        base_temperature = self.base_temperature
        await self._setpoint_shift.set(validated_offset)
        # broadcast new target temperature and set internally
        if self.target_temperature.writable and base_temperature is not None:
            await self.target_temperature.set(base_temperature + self.setpoint_shift)

    @property
    def target_temperature_max(self):
        """Return the highest possible target temperature."""
        if self.max_temp is not None:
            return self.max_temp
        if self.initialized_for_setpoint_shift_calculations:
            return self.base_temperature + self.setpoint_shift_max
        return None

    @property
    def target_temperature_min(self):
        """Return the lowest possible target temperature."""
        if self.min_temp is not None:
            return self.min_temp
        if self.initialized_for_setpoint_shift_calculations:
            return self.base_temperature + self.setpoint_shift_min
        return None

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)
        if self.mode is not None:
            await self.mode.process_group_write(telegram)

    async def sync(self, wait_for_result=False):
        """Read states of device from KNX bus."""
        await super().sync(wait_for_result=wait_for_result)
        if self.mode is not None:
            await self.mode.sync(wait_for_result=wait_for_result)

    def __str__(self):
        """Return object as readable string."""
        return (
            '<Climate name="{}" '
            'temperature="{}" '
            'target_temperature="{}" '
            'temperature_step="{}" '
            'setpoint_shift="{}" '
            'setpoint_shift_max="{}" '
            'setpoint_shift_min="{}" '
            'group_address_on_off="{}" '
            "/>".format(
                self.name,
                self.temperature.group_addr_str(),
                self.target_temperature.group_addr_str(),
                self.temperature_step,
                self._setpoint_shift.group_addr_str(),
                self.setpoint_shift_max,
                self.setpoint_shift_min,
                self.on.group_addr_str(),
            )
        )
