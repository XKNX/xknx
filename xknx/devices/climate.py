"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
from xknx.exceptions import CouldNotParseTelegram, DeviceIllegalValue
from xknx.knx import (DPTArray, DPTBinary, DPTControllerStatus, DPTHVACMode,
                      GroupAddress, HVACOperationMode)

from .device import Device
from .remote_value_temp import RemoteValueTemp
from .remote_value_1count import RemoteValue1Count


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
                 group_address_setpoint_shift=None,
                 group_address_setpoint_shift_state=None,
                 setpoint_shift_step=DEFAULT_SETPOINT_SHIFT_STEP,
                 setpoint_shift_max=DEFAULT_SETPOINT_SHIFT_MAX,
                 setpoint_shift_min=DEFAULT_SETPOINT_SHIFT_MIN,
                 group_address_operation_mode=None,
                 group_address_operation_mode_state=None,
                 group_address_operation_mode_protection=None,
                 group_address_operation_mode_night=None,
                 group_address_operation_mode_comfort=None,
                 group_address_controller_status=None,
                 group_address_controller_status_state=None,
                 device_updated_cb=None):
        """Initialize Climate class."""
        # pylint: disable=too-many-arguments, too-many-locals
        super(Climate, self).__init__(xknx, name, device_updated_cb)
        if isinstance(group_address_operation_mode, (str, int)):
            group_address_operation_mode = GroupAddress(group_address_operation_mode)
        if isinstance(group_address_operation_mode_state, (str, int)):
            group_address_operation_mode_state = GroupAddress(group_address_operation_mode_state)
        if isinstance(group_address_operation_mode_protection, (str, int)):
            group_address_operation_mode_protection = GroupAddress(group_address_operation_mode_protection)
        if isinstance(group_address_operation_mode_night, (str, int)):
            group_address_operation_mode_night = GroupAddress(group_address_operation_mode_night)
        if isinstance(group_address_operation_mode_comfort, (str, int)):
            group_address_operation_mode_comfort = GroupAddress(group_address_operation_mode_comfort)
        if isinstance(group_address_controller_status, (str, int)):
            group_address_controller_status = GroupAddress(group_address_controller_status)
        if isinstance(group_address_controller_status_state, (str, int)):
            group_address_controller_status_state = GroupAddress(group_address_controller_status_state)

        self.group_address_operation_mode = group_address_operation_mode
        self.group_address_operation_mode_state = group_address_operation_mode_state
        self.group_address_operation_mode_protection = group_address_operation_mode_protection
        self.group_address_operation_mode_night = group_address_operation_mode_night
        self.group_address_operation_mode_comfort = group_address_operation_mode_comfort
        self.group_address_controller_status = group_address_controller_status
        self.group_address_controller_status_state = group_address_controller_status_state

        self.operation_mode = HVACOperationMode.STANDBY

        self.temperature = RemoteValueTemp(
            xknx,
            group_address_temperature,
            device_name=self.name,
            after_update_cb=self.after_update)
        self.target_temperature = RemoteValueTemp(
            xknx,
            group_address_target_temperature,
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

        self.supports_operation_mode = \
            group_address_operation_mode is not None or \
            group_address_operation_mode_state is not None or \
            group_address_operation_mode_protection is not None or \
            group_address_operation_mode_night is not None or \
            group_address_operation_mode_comfort is not None or \
            group_address_controller_status is not None or \
            group_address_controller_status_state is not None

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        # pylint: disable=too-many-locals
        group_address_temperature = \
            config.get('group_address_temperature')
        group_address_target_temperature = \
            config.get('group_address_target_temperature')
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
        group_address_operation_mode = \
            config.get('group_address_operation_mode')
        group_address_operation_mode_state = \
            config.get('group_address_operation_mode_state')
        group_address_operation_mode_protection = \
            config.get('group_address_operation_mode_protection')
        group_address_operation_mode_night = \
            config.get('group_address_operation_mode_night')
        group_address_operation_mode_comfort = \
            config.get('group_address_operation_mode_comfort')
        group_address_controller_status = \
            config.get('group_address_controller_status')
        group_address_controller_status_state = \
            config.get('group_address_controller_status_state')
        return cls(xknx,
                   name,
                   group_address_temperature=group_address_temperature,
                   group_address_target_temperature=group_address_target_temperature,
                   group_address_setpoint_shift=group_address_setpoint_shift,
                   group_address_setpoint_shift_state=group_address_setpoint_shift_state,
                   setpoint_shift_step=setpoint_shift_step,
                   setpoint_shift_max=setpoint_shift_max,
                   setpoint_shift_min=setpoint_shift_min,
                   group_address_operation_mode=group_address_operation_mode,
                   group_address_operation_mode_state=group_address_operation_mode_state,
                   group_address_operation_mode_protection=group_address_operation_mode_protection,
                   group_address_operation_mode_night=group_address_operation_mode_night,
                   group_address_operation_mode_comfort=group_address_operation_mode_comfort,
                   group_address_controller_status=group_address_controller_status,
                   group_address_controller_status_state=group_address_controller_status_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.temperature.has_group_address(group_address) or \
            self.target_temperature.has_group_address(group_address) or \
            self.setpoint_shift.has_group_address(group_address) or \
            self.group_address_operation_mode == group_address or \
            self.group_address_operation_mode_state == group_address or \
            self.group_address_operation_mode_protection == group_address or \
            self.group_address_operation_mode_night == group_address or \
            self.group_address_operation_mode_comfort == group_address or \
            self.group_address_controller_status == group_address or \
            self.group_address_controller_status_state == group_address

    async def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            await self.after_update()

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
        elif setpoint_shift < self.setpoint_shift_min:
            raise DeviceIllegalValue("setpoint_shift_min exceeded", setpoint_shift)

        await self.setpoint_shift.set(setpoint_shift)

    @property
    def target_temperature_max(self):
        """Return the maxium possible target temperature."""
        if not self.initialized_for_setpoint_shift_calculations:
            return None
        return (self.target_temperature.value -
                self.setpoint_shift.value * self.setpoint_shift_step +
                self.setpoint_shift_max * self.setpoint_shift_step)

    @property
    def target_temperature_min(self):
        """Return the minimum possible target temperature."""
        if not self.initialized_for_setpoint_shift_calculations:
            return None
        return (self.target_temperature.value -
                self.setpoint_shift.value * self.setpoint_shift_step +
                self.setpoint_shift_min * self.setpoint_shift_step)

    async def set_operation_mode(self, operation_mode):
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if not self.supports_operation_mode:
            raise DeviceIllegalValue("operation mode not supported", operation_mode)
        if self.group_address_operation_mode is not None:
            await self.send(
                self.group_address_operation_mode,
                DPTArray(DPTHVACMode.to_knx(operation_mode)))
        if self.group_address_operation_mode_protection is not None:
            protection_mode = operation_mode == HVACOperationMode.FROST_PROTECTION
            await self.send(
                self.group_address_operation_mode_protection,
                DPTBinary(protection_mode))
        if self.group_address_operation_mode_night is not None:
            night_mode = operation_mode == HVACOperationMode.NIGHT
            await self.send(
                self.group_address_operation_mode_night,
                DPTBinary(night_mode))
        if self.group_address_operation_mode_comfort is not None:
            comfort_mode = operation_mode == HVACOperationMode.COMFORT
            await self.send(
                self.group_address_operation_mode_comfort,
                DPTBinary(comfort_mode))
        if self.group_address_controller_status is not None:
            await self.send(
                self.group_address_controller_status,
                DPTArray(DPTControllerStatus.to_knx(operation_mode)))
        await self._set_internal_operation_mode(operation_mode)

    def get_supported_operation_modes(self):
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []

        # All operation modes supported
        if self.group_address_operation_mode is not None:
            return list(HVACOperationMode)
        if self.group_address_controller_status is not None:
            return list(filter(lambda x: x != HVACOperationMode.AUTO, HVACOperationMode))

        # Operation modes only supported partially
        operation_modes = []
        if self.group_address_operation_mode_comfort:
            operation_modes.append(HVACOperationMode.COMFORT)
        operation_modes.append(HVACOperationMode.STANDBY)
        if self.group_address_operation_mode_night:
            operation_modes.append(HVACOperationMode.NIGHT)
        if self.group_address_operation_mode_protection:
            operation_modes.append(HVACOperationMode.FROST_PROTECTION)
        return operation_modes

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if self.supports_operation_mode and \
                telegram.group_address == self.group_address_operation_mode or \
                telegram.group_address == self.group_address_operation_mode_state:
            await self._process_operation_mode(telegram)
        elif self.supports_operation_mode and \
                telegram.group_address == self.group_address_controller_status or \
                telegram.group_address == self.group_address_controller_status_state:
            await self._process_controller_status(telegram)
        # Note: telegrams setting splitted up operation modes are not yet implemented

        await self.temperature.process(telegram)
        await self.target_temperature.process(telegram)
        await self.setpoint_shift.process(telegram)

    async def _process_operation_mode(self, telegram):
        """Process incoming telegram for operation mode."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram("invalid payload", payload=telegram.payload, device_name=self.name)
        operation_mode = DPTHVACMode.from_knx(telegram.payload.value)
        await self._set_internal_operation_mode(operation_mode)

    async def _process_controller_status(self, telegram):
        """Process incoming telegram for controller status."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram("invalid payload", payload=telegram.payload, device_name=self.name)
        operation_mode = DPTControllerStatus.from_knx(telegram.payload.value)
        await self._set_internal_operation_mode(operation_mode)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.temperature.state_addresses())
        state_addresses.extend(self.target_temperature.state_addresses())
        state_addresses.extend(self.setpoint_shift.state_addresses())
        if self.supports_operation_mode:
            if self.group_address_operation_mode_state:
                state_addresses.append(self.group_address_operation_mode_state)
            elif self.group_address_operation_mode:
                state_addresses.append(self.group_address_operation_mode)
            if self.group_address_controller_status_state:
                state_addresses.append(self.group_address_controller_status_state)
            elif self.group_address_controller_status:
                state_addresses.append(self.group_address_controller_status)
            # Note: telegrams setting splitted up operation modes are not yet implemented
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
            'group_address_operation_mode="{7}" ' \
            'group_address_operation_mode_state="{8}" ' \
            'group_address_controller_status="{9}" ' \
            'group_address_controller_status_state="{10}" ' \
            '/>' \
            .format(
                self.name,
                self.temperature.group_addr_str(),
                self.target_temperature.group_addr_str(),
                self.setpoint_shift.group_addr_str(),
                self.setpoint_shift_step,
                self.setpoint_shift_max,
                self.setpoint_shift_min,
                self.group_address_operation_mode,
                self.group_address_operation_mode_state,
                self.group_address_controller_status,
                self.group_address_controller_status_state)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
