"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
from xknx.exceptions import DeviceIllegalValue
from xknx.knx import GroupAddress

from .climate_mode import ClimateMode
from .device import Device
from .remote_value_1count import RemoteValue1Count
from .remote_value_switch import RemoteValueSwitch
from .remote_value_temp import RemoteValueTemp

DEFAULT_SETPOINT_SHIFT_STEP = 0.5
DEFAULT_SETPOINT_SHIFT_MAX = 6
DEFAULT_SETPOINT_SHIFT_MIN = -6


class SetpointShiftValue(RemoteValue1Count):
    """Class for managing setpoint_shift values."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None,
                 setpoint_shift_step=DEFAULT_SETPOINT_SHIFT_STEP,
                 min_kelvin=DEFAULT_SETPOINT_SHIFT_MIN,
                 max_kelvin=DEFAULT_SETPOINT_SHIFT_MAX):
        """Initialize SepointShift class."""
        # pylint: disable=too-many-arguments
        self.setpoint_shift_step = setpoint_shift_step
        self.min_kelvin = min_kelvin
        self.max_kelvin = max_kelvin

        if self.setpoint_shift_step is None:
            self.setpoint_shift_step = DEFAULT_SETPOINT_SHIFT_STEP
        if self.min_kelvin is None:
            self.min_kelvin = DEFAULT_SETPOINT_SHIFT_MIN
        if self.max_kelvin is None:
            self.max_kelvin = DEFAULT_SETPOINT_SHIFT_MAX

        super().__init__(xknx,
                         group_address,
                         group_address_state,
                         device_name,
                         after_update_cb)

    @property
    def value(self):
        """Return current value in Kelvin."""
        if super().value is not None:
            return super().value * self.setpoint_shift_step
        return None

    async def set(self, value):
        """Set new value from Kelvin."""
        if value > self.max_kelvin:
            raise DeviceIllegalValue("setpoint_shift_max exceeded", value)
        elif value < self.min_kelvin:
            raise DeviceIllegalValue("setpoint_shift_min exceeded", value)

        raw_value = int(value / self.setpoint_shift_step)
        await super().set(raw_value)


class Climate(Device):
    """Class for managing the climate."""

    # pylint: disable=too-many-instance-attributes,invalid-name
    def __init__(self,
                 xknx,
                 name,
                 group_address_temperature=None,
                 group_address_target_temperature=None,
                 group_address_target_temperature_state=None,
                 group_address_base_temperature_state=None,
                 group_address_setpoint_shift=None,
                 group_address_setpoint_shift_state=None,
                 setpoint_shift_step=None,
                 setpoint_shift_max=None,
                 setpoint_shift_min=None,
                 group_address_on_off=None,
                 group_address_on_off_state=None,
                 min_temp=None,
                 max_temp=None,
                 mode=None,
                 device_updated_cb=None):
        """Initialize Climate class."""
        # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        super().__init__(xknx, name, device_updated_cb)
        if isinstance(group_address_on_off, (str, int)):
            group_address_on_off = GroupAddress(group_address_on_off)
        if isinstance(group_address_on_off_state, (str, int)):
            group_address_on_off_state = GroupAddress(group_address_on_off_state)

        self.group_address_on_off = group_address_on_off
        self.group_address_on_off_state = group_address_on_off_state

        self.min_temp = min_temp
        self.max_temp = max_temp

        self.temperature = RemoteValueTemp(
            xknx,
            group_address_state=group_address_temperature,
            device_name=self.name,
            after_update_cb=self.after_update)
        self._target_temperature = RemoteValueTemp(
            xknx,
            group_address_target_temperature,
            group_address_target_temperature_state,
            device_name=self.name,
            after_update_cb=self.after_update)
        self._base_temperature = RemoteValueTemp(
            xknx,
            None,
            group_address_base_temperature_state,
            device_name=self.name,
            after_update_cb=self.after_update)
        self._setpoint_shift = SetpointShiftValue(
            xknx,
            group_address_setpoint_shift,
            group_address_setpoint_shift_state,
            device_name=self.name,
            after_update_cb=self.after_update,
            setpoint_shift_step=setpoint_shift_step,
            min_kelvin=setpoint_shift_min,
            max_kelvin=setpoint_shift_max)

        self.supports_on_off = \
            group_address_on_off is not None or \
            group_address_on_off_state is not None

        self.on = RemoteValueSwitch(
            xknx,
            group_address_on_off,
            group_address_on_off_state,
            self.name,
            self.after_update)

        self.mode = mode

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        # pylint: disable=too-many-locals
        group_address_temperature = \
            config.get('group_address_temperature')
        group_address_target_temperature = \
            config.get('group_address_target_temperature')
        group_address_target_temperature_state = \
            config.get('group_address_target_temperature_state')
        group_address_base_temperature_state = \
            config.get('group_address_base_temperature_state')
        group_address_setpoint_shift = \
            config.get('group_address_setpoint_shift')
        group_address_setpoint_shift_state = \
            config.get('group_address_setpoint_shift_state')
        setpoint_shift_step = \
            config.get('setpoint_shift_step')
        setpoint_shift_max = \
            config.get('setpoint_shift_max')
        setpoint_shift_min = \
            config.get('setpoint_shift_min')
        group_address_on_off = \
            config.get('group_address_on_off')
        group_address_on_off_state = \
            config.get('group_address_on_off_state')
        min_temp = config.get('min_temp')
        max_temp = config.get('max_temp')

        climate_mode = None
        if "mode" in config:
            climate_mode = ClimateMode.from_config(
                xknx=xknx,
                name=None,
                config=config['mode'])

        return cls(xknx,
                   name,
                   group_address_temperature=group_address_temperature,
                   group_address_target_temperature=group_address_target_temperature,
                   group_address_target_temperature_state=group_address_target_temperature_state,
                   group_address_base_temperature_state=group_address_base_temperature_state,
                   group_address_setpoint_shift=group_address_setpoint_shift,
                   group_address_setpoint_shift_state=group_address_setpoint_shift_state,
                   setpoint_shift_step=setpoint_shift_step,
                   setpoint_shift_max=setpoint_shift_max,
                   setpoint_shift_min=setpoint_shift_min,
                   group_address_on_off=group_address_on_off,
                   group_address_on_off_state=group_address_on_off_state,
                   min_temp=min_temp,
                   max_temp=max_temp,
                   mode=climate_mode)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        if self.mode is not None and self.mode.has_group_address(group_address):
            return True
        return self.temperature.has_group_address(group_address) or \
            self._target_temperature.has_group_address(group_address) or \
            self._base_temperature.has_group_address(group_address) or \
            self._setpoint_shift.has_group_address(group_address) or \
            self.on.has_group_address(group_address)

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
        if self.setpoint_shift is None:
            return False
        # Test if target temperature has a writable group address
        # if self._target_temperature.group_address is not None:
        #     return False
        if not (self._target_temperature.initialized or
                self._base_temperature.initialized):
            return False
        if self.target_temperature is None and \
                self.base_temperature is None:
            return False
        return True

    @property
    def target_temperature(self):
        """Return target temperature read from bus or calculated if not available."""
        if self._target_temperature.value is not None:
            return self._target_temperature.value
        if self._base_temperature.value is not None and \
                self._setpoint_shift.value is not None:
            return self._base_temperature.value + self._setpoint_shift.value
        return None

    async def set_target_temperature(self, target_temperature):
        """Send new target temperature or setpoint_shift to KNX bus."""
        if self.initialized_for_setpoint_shift_calculations:
            temperature_delta = target_temperature-self.base_temperature
            await self.set_setpoint_shift(temperature_delta)
        # broadcast new target temperature and set internally
        await self._target_temperature.set(target_temperature)

    @property
    def base_temperature(self):
        """Return base temperature read from bus or calculated if not available."""
        if self._base_temperature.value is not None:
            return self._base_temperature.value
        if self._target_temperature.value is not None and \
                self._setpoint_shift.value is not None:
            return self._target_temperature.value - self._setpoint_shift.value
        return None

    @property
    def setpoint_shift(self):
        """Return current offset from base temperature in Kelvin."""
        return self._setpoint_shift.value

    async def set_setpoint_shift(self, offset):
        """Send new temperature offset to KNX bus."""
        await self._setpoint_shift.set(offset)

    @property
    def target_temperature_max(self):
        """Return the maxium possible target temperature."""
        if self.max_temp is not None:
            return self.max_temp
        if self.initialized_for_setpoint_shift_calculations:
            return self.base_temperature + self._setpoint_shift.max_kelvin
        return None

    @property
    def target_temperature_min(self):
        """Return the minimum possible target temperature."""
        if self.min_temp is not None:
            return self.min_temp
        if self.initialized_for_setpoint_shift_calculations:
            return self.base_temperature + self._setpoint_shift.min_kelvin
        return None

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self.temperature.process(telegram)
        await self._target_temperature.process(telegram)
        await self._base_temperature.process(telegram)
        await self._setpoint_shift.process(telegram)
        await self.on.process(telegram)
        if self.mode is not None:
            await self.mode.process_group_write(telegram)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.temperature.state_addresses())
        state_addresses.extend(self._target_temperature.state_addresses())
        state_addresses.extend(self._base_temperature.state_addresses())
        state_addresses.extend(self._setpoint_shift.state_addresses())
        if self.supports_on_off:
            state_addresses.extend(self.on.state_addresses())
        if self.mode is not None:
            state_addresses.extend(self.mode.state_addresses())
        return state_addresses

    def __str__(self):
        """Return object as readable string."""
        return '<Climate name="{0}" ' \
            'temperature="{1}" ' \
            'target_temperature="{2}" ' \
            'base_temperature="{3}" ' \
            'setpoint_shift="{4}" ' \
            'setpoint_shift_step="{5}" ' \
            'setpoint_shift_max="{6}" ' \
            'setpoint_shift_min="{7}" ' \
            'group_address_on_off="{8}" ' \
            '/>' \
            .format(
                self.name,
                self.temperature.group_addr_str(),
                self._target_temperature.group_addr_str(),
                self._base_temperature.group_addr_str(),
                self._setpoint_shift.group_addr_str(),
                self._setpoint_shift.setpoint_shift_step,
                self._setpoint_shift.max_kelvin,
                self._setpoint_shift.min_kelvin,
                self.on.group_addr_str())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
