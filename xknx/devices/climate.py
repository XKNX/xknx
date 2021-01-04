"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
from enum import Enum
import logging
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union, cast

from xknx.remote_value import (
    RemoteValueSetpointShift,
    RemoteValueSwitch,
    RemoteValueTemp,
)

from .climate_mode import ClimateMode
from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.remote_value import RemoteValue
    from xknx.telegram import Telegram
    from xknx.telegram.address import GroupAddress, GroupAddressableType
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


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
        xknx: "XKNX",
        name: str,
        group_address_temperature: Optional["GroupAddressableType"] = None,
        group_address_target_temperature: Optional["GroupAddressableType"] = None,
        group_address_target_temperature_state: Optional["GroupAddressableType"] = None,
        group_address_setpoint_shift: Optional["GroupAddressableType"] = None,
        group_address_setpoint_shift_state: Optional["GroupAddressableType"] = None,
        setpoint_shift_mode: SetpointShiftMode = DEFAULT_SETPOINT_SHIFT_MODE,
        setpoint_shift_max: float = DEFAULT_SETPOINT_SHIFT_MAX,
        setpoint_shift_min: float = DEFAULT_SETPOINT_SHIFT_MIN,
        temperature_step: float = DEFAULT_TEMPERATURE_STEP,
        group_address_on_off: Optional["GroupAddressableType"] = None,
        group_address_on_off_state: Optional["GroupAddressableType"] = None,
        on_off_invert: bool = False,
        min_temp: Optional[float] = None,
        max_temp: Optional[float] = None,
        mode: Optional[ClimateMode] = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
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

        self._setpoint_shift: Union[RemoteValueTemp, RemoteValueSetpointShift]
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

    def _iter_remote_values(self) -> Iterator["RemoteValue"]:
        """Iterate the devices RemoteValue classes."""
        yield from (
            self.temperature,
            self.target_temperature,
            self._setpoint_shift,
            self.on,
        )

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Any) -> "Climate":
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
                xknx=xknx, name=f"{name}_mode", config=config["mode"]
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

    def has_group_address(self, group_address: "GroupAddress") -> bool:
        """Test if device has given group address."""
        if self.mode is not None and self.mode.has_group_address(group_address):
            return True
        return super().has_group_address(group_address)

    @property
    def is_on(self) -> bool:
        """Return power status."""
        # None will return False
        return bool(self.on.value)

    async def turn_on(self) -> None:
        """Set power status to on."""
        await self.on.on()

    async def turn_off(self) -> None:
        """Set power status to off."""
        await self.on.off()

    @property
    def initialized_for_setpoint_shift_calculations(self) -> bool:
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
    def base_temperature(self) -> Optional[float]:
        """
        Return the base temperature when setpoint_shift is initialized.

        Base temperature is the default temperature (setpoint-shift=0) for the active climate mode.
        As this value is usually not available via KNX, we have to derive this from the current
        target temperature and the current set point shift.
        """
        if self.initialized_for_setpoint_shift_calculations:
            return cast(float, self.target_temperature.value - self.setpoint_shift)
        return None

    @property
    def setpoint_shift(self) -> Optional[float]:
        """Return current offset from base temperature in Kelvin."""
        return self._setpoint_shift.value  # type: ignore

    def validate_value(
        self, value: float, min_value: Optional[float], max_value: Optional[float]
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
    def target_temperature_max(self) -> Optional[float]:
        """Return the highest possible target temperature."""
        if self.max_temp is not None:
            return self.max_temp
        if self.base_temperature is not None:
            # implies initialized_for_setpoint_shift_calculations
            return self.base_temperature + self.setpoint_shift_max
        return None

    @property
    def target_temperature_min(self) -> Optional[float]:
        """Return the lowest possible target temperature."""
        if self.min_temp is not None:
            return self.min_temp
        if self.base_temperature is not None:
            # implies initialized_for_setpoint_shift_calculations
            return self.base_temperature + self.setpoint_shift_min
        return None

    async def process_group_write(self, telegram: "Telegram") -> None:
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
