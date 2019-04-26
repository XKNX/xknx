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


class Climate(Device):
    """Class for managing the climate."""

    # pylint: disable=too-many-instance-attributes,invalid-name

    DEFAULT_SETPOINT_SHIFT_STEP = 0.5
    DEFAULT_SETPOINT_SHIFT_MAX = 6
    DEFAULT_SETPOINT_SHIFT_MIN = -6

    def __init__(self,
                 xknx,
                 name,
                 group_address_temperature=None,
                 group_address_target_temperature=None,
                 group_address_target_temperature_state=None,
                 group_address_setpoint_shift=None,
                 group_address_setpoint_shift_state=None,
                 setpoint_shift_step=DEFAULT_SETPOINT_SHIFT_STEP,
                 setpoint_shift_max=DEFAULT_SETPOINT_SHIFT_MAX,
                 setpoint_shift_min=DEFAULT_SETPOINT_SHIFT_MIN,
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
        self.target_temperature = RemoteValueTemp(
            xknx,
            group_address_target_temperature,
            group_address_target_temperature_state,
            device_name=self.name,
            after_update_cb=self.after_update)
        self.setpoint_shift = RemoteValue1Count(
            xknx,
            group_address_setpoint_shift,
            group_address_setpoint_shift_state,
            device_name=self.name,
            after_update_cb=self.after_update)

        self.setpoint_shift_step = setpoint_shift_step
        self.setpoint_shift_max = setpoint_shift_max
        self.setpoint_shift_min = setpoint_shift_min

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
        group_address_setpoint_shift = \
            config.get('group_address_setpoint_shift')
        group_address_setpoint_shift_state = \
            config.get('group_address_setpoint_shift_state')
        setpoint_shift_step = \
            config.get('setpoint_shift_step', cls.DEFAULT_SETPOINT_SHIFT_STEP)
        setpoint_shift_max = \
            config.get('setpoint_shift_max', cls.DEFAULT_SETPOINT_SHIFT_MAX)
        setpoint_shift_min = \
            config.get('setpoint_shift_min', cls.DEFAULT_SETPOINT_SHIFT_MIN)
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
            self.target_temperature.has_group_address(group_address) or \
            self.setpoint_shift.has_group_address(group_address) or \
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
        if not self.setpoint_shift.initialized:
            return False
        if self.setpoint_shift.value is None:
            return False
        if not self.target_temperature.initialized:
            return False
        if self.target_temperature.value is None:
            return False
        return True

    async def set_target_temperature(self, target_temperature):
        """Calculate setpoint shift shift and send it to  KNX bus."""
        if self.initialized_for_setpoint_shift_calculations:
            await self.set_target_temperature_setpoint_shift(target_temperature)
        # broadcast new target temperature and set internally
        await self.target_temperature.set(target_temperature)

    async def set_target_temperature_setpoint_shift(self, target_temperature):
        """Set target temperature via setpoint_shift group address."""
        temperature_delta = target_temperature-self.target_temperature.value
        setpoint_shift_delta = int(temperature_delta/self.setpoint_shift_step)
        setpoint_shift = self.setpoint_shift.value + setpoint_shift_delta

        if setpoint_shift > self.setpoint_shift_max:
            raise DeviceIllegalValue("setpoint_shift_max exceeded", setpoint_shift)
        if setpoint_shift < self.setpoint_shift_min:
            raise DeviceIllegalValue("setpoint_shift_min exceeded", setpoint_shift)

        await self.setpoint_shift.set(setpoint_shift)

    @property
    def target_temperature_max(self):
        """Return the maxium possible target temperature."""
        if self.max_temp is not None:
            return self.max_temp
        if not self.initialized_for_setpoint_shift_calculations:
            return None
        return (self.target_temperature.value -
                self.setpoint_shift.value * self.setpoint_shift_step +
                self.setpoint_shift_max * self.setpoint_shift_step)

    @property
    def target_temperature_min(self):
        """Return the minimum possible target temperature."""
        if self.min_temp is not None:
            return self.min_temp
        if not self.initialized_for_setpoint_shift_calculations:
            return None
        return (self.target_temperature.value -
                self.setpoint_shift.value * self.setpoint_shift_step +
                self.setpoint_shift_min * self.setpoint_shift_step)

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self.temperature.process(telegram)
        await self.target_temperature.process(telegram)
        await self.setpoint_shift.process(telegram)
        await self.on.process(telegram)
        if self.mode is not None:
            await self.mode.process_group_write(telegram)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.temperature.state_addresses())
        state_addresses.extend(self.target_temperature.state_addresses())
        state_addresses.extend(self.setpoint_shift.state_addresses())
        if self.supports_on_off:
            state_addresses.extend(self.on.state_addresses())
        if self.mode is not None:
            state_addresses.extend(self.mode.state_addresses())
        return state_addresses

    def __str__(self):
        """Return object as readable string."""
        return '<Climate name="{0}" ' \
            'temperature="{1}"  ' \
            'target_temperature="{2}"  ' \
            'setpoint_shift="{3}" ' \
            'setpoint_shift_step="{4}" ' \
            'setpoint_shift_max="{5}" ' \
            'setpoint_shift_min="{6}" ' \
            'group_address_on_off="{7}" ' \
            '/>' \
            .format(
                self.name,
                self.temperature.group_addr_str(),
                self.target_temperature.group_addr_str(),
                self.setpoint_shift.group_addr_str(),
                self.setpoint_shift_step,
                self.setpoint_shift_max,
                self.setpoint_shift_min,
                self.on.group_addr_str())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
