"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterator

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueScaling,
    RemoteValueSetpointShift,
    RemoteValueSwitch,
    RemoteValueTemp,
)
from xknx.remote_value.remote_value_setpoint_shift import SetpointShiftMode

from .climate_mode import ClimateMode
from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.telegram.address import DeviceGroupAddress
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


DEFAULT_SETPOINT_SHIFT_MAX = 6
DEFAULT_SETPOINT_SHIFT_MIN = -6
DEFAULT_TEMPERATURE_STEP = 0.1


class Climate(Device):
    """Class for managing the climate."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_temperature: GroupAddressesType | None = None,
        group_address_target_temperature: GroupAddressesType | None = None,
        group_address_target_temperature_state: GroupAddressesType | None = None,
        group_address_setpoint_shift: GroupAddressesType | None = None,
        group_address_setpoint_shift_state: GroupAddressesType | None = None,
        setpoint_shift_mode: SetpointShiftMode | None = None,
        setpoint_shift_max: float = DEFAULT_SETPOINT_SHIFT_MAX,
        setpoint_shift_min: float = DEFAULT_SETPOINT_SHIFT_MIN,
        temperature_step: float = DEFAULT_TEMPERATURE_STEP,
        group_address_on_off: GroupAddressesType | None = None,
        group_address_on_off_state: GroupAddressesType | None = None,
        on_off_invert: bool = False,
        group_address_active_state: GroupAddressesType | None = None,
        group_address_command_value_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        min_temp: float | None = None,
        max_temp: float | None = None,
        mode: ClimateMode | None = None,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize Climate class."""
        super().__init__(xknx, name, device_updated_cb)

        self.min_temp = min_temp
        self.max_temp = max_temp
        self.setpoint_shift_min = setpoint_shift_min
        self.setpoint_shift_max = setpoint_shift_max
        self.temperature_step = temperature_step

        self.temperature = RemoteValueTemp(
            xknx,
            group_address_state=group_address_temperature,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Current temperature",
            after_update_cb=self.after_update,
        )

        self.target_temperature = RemoteValueTemp(
            xknx,
            group_address_target_temperature,
            group_address_target_temperature_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Target temperature",
            after_update_cb=self.after_update,
        )

        self._setpoint_shift = RemoteValueSetpointShift(
            xknx,
            group_address_setpoint_shift,
            group_address_setpoint_shift_state,
            sync_state=sync_state,
            device_name=self.name,
            after_update_cb=self.after_update,
            setpoint_shift_mode=setpoint_shift_mode,
            setpoint_shift_step=self.temperature_step,
        )

        self.supports_on_off = (
            group_address_on_off is not None or group_address_on_off_state is not None
        )

        self.on = RemoteValueSwitch(  # pylint: disable=invalid-name
            xknx,
            group_address_on_off,
            group_address_on_off_state,
            sync_state=sync_state,
            device_name=self.name,
            after_update_cb=self.after_update,
            invert=on_off_invert,
        )

        self.active = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_active_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Active",
            after_update_cb=self.after_update,
        )

        self.command_value = RemoteValueScaling(
            xknx,
            group_address_state=group_address_command_value_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Command value",
            after_update_cb=self.after_update,
        )

        self.mode = mode

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.temperature
        yield self.target_temperature
        yield self._setpoint_shift
        yield self.on
        yield self.active
        yield self.command_value

    def has_group_address(self, group_address: DeviceGroupAddress) -> bool:
        """Test if device has given group address."""
        if self.mode is not None and self.mode.has_group_address(group_address):
            return True
        return super().has_group_address(group_address)

    @property
    def is_on(self) -> bool:
        """Return power status."""
        # None will return False
        return bool(self.on.value)

    @property
    def is_active(self) -> bool | None:
        """Return if currently active. None if unknown."""
        if self.active.value is not None:
            return self.active.value
        if self.command_value.value is not None:
            return bool(self.command_value.value)
        return None

    async def turn_on(self) -> None:
        """Set power status to on."""
        await self.on.on()

    async def turn_off(self) -> None:
        """Set power status to off."""
        await self.on.off()

    @property
    def initialized_for_setpoint_shift_calculations(self) -> bool:
        """Test if object is initialized for setpoint shift calculations."""
        if (
            self._setpoint_shift.initialized
            and self._setpoint_shift.value is not None
            and self.target_temperature.initialized
            and self.target_temperature.value is not None
        ):
            return True
        return False

    async def set_target_temperature(self, target_temperature: float) -> None:
        """Send new target temperature or setpoint_shift to KNX bus."""
        if self.base_temperature is not None:
            # implies initialized_for_setpoint_shift_calculations
            temperature_delta = target_temperature - self.base_temperature
            await self.set_setpoint_shift(temperature_delta)
        else:
            validated_temp = self.validate_value(
                target_temperature, self.min_temp, self.max_temp
            )
            await self.target_temperature.set(validated_temp)

    @property
    def base_temperature(self) -> float | None:
        """
        Return the base temperature when setpoint_shift is initialized.

        Base temperature is the default temperature (setpoint-shift=0) for the active climate mode.
        As this value is usually not available via KNX, we have to derive this from the current
        target temperature and the current set point shift.
        """
        # implies self.initialized_for_setpoint_shift_calculations in a mypy compatible way:
        if (
            self.target_temperature.value is not None
            and self._setpoint_shift.value is not None
        ):
            return self.target_temperature.value - self._setpoint_shift.value
        return None

    @property
    def setpoint_shift(self) -> float | None:
        """Return current offset from base temperature in Kelvin."""
        return self._setpoint_shift.value

    def validate_value(
        self, value: float, min_value: float | None, max_value: float | None
    ) -> float:
        """Check boundaries of temperature and return valid temperature value."""
        if (min_value is not None) and (value < min_value):
            logger.warning("Min value exceeded at %s: %s", self.name, value)
            return min_value
        if (max_value is not None) and (value > max_value):
            logger.warning("Max value exceeded at %s: %s", self.name, value)
            return max_value
        return value

    async def set_setpoint_shift(self, offset: float) -> None:
        """Send new temperature offset to KNX bus."""
        validated_offset = self.validate_value(
            offset, self.setpoint_shift_min, self.setpoint_shift_max
        )
        base_temperature = self.base_temperature
        await self._setpoint_shift.set(validated_offset)
        # broadcast new target temperature and set internally
        if self.target_temperature.writable and base_temperature is not None:
            await self.target_temperature.set(base_temperature + validated_offset)

    @property
    def target_temperature_max(self) -> float | None:
        """Return the highest possible target temperature."""
        if self.max_temp is not None:
            return self.max_temp
        if self.base_temperature is not None:
            # implies initialized_for_setpoint_shift_calculations
            return self.base_temperature + self.setpoint_shift_max
        return None

    @property
    def target_temperature_min(self) -> float | None:
        """Return the lowest possible target temperature."""
        if self.min_temp is not None:
            return self.min_temp
        if self.base_temperature is not None:
            # implies initialized_for_setpoint_shift_calculations
            return self.base_temperature + self.setpoint_shift_min
        return None

    async def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)
        if self.mode is not None:
            await self.mode.process_group_write(telegram)

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read states of device from KNX bus."""
        await super().sync(wait_for_result=wait_for_result)
        if self.mode is not None:
            await self.mode.sync(wait_for_result=wait_for_result)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Climate name="{self.name}" '
            f"temperature={self.temperature.group_addr_str()} "
            f"target_temperature={self.target_temperature.group_addr_str()} "
            f'temperature_step="{self.temperature_step}" '
            f"setpoint_shift={self._setpoint_shift.group_addr_str()} "
            f'setpoint_shift_max="{self.setpoint_shift_max}" '
            f'setpoint_shift_min="{self.setpoint_shift_min}" '
            f"group_address_on_off={self.on.group_addr_str()} "
            "/>"
        )
