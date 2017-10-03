"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
import asyncio
from xknx.knx import Address, DPTBinary, DPTArray, \
    HVACOperationMode, DPTControllerStatus, DPTHVACMode
from xknx.exceptions import CouldNotParseTelegram
from .device import Device
from .remote_value import RemoteValueTemp, RemoteValue1Count


class Climate(Device):
    """Class for managing the climate."""

    # pylint: disable=too-many-instance-attributes,invalid-name

    def __init__(self,
                 xknx,
                 name,
                 group_address_temperature=None,
                 group_address_target_temperature=None,
                 group_address_setpoint=None,
                 group_address_setpoint_shift=None,
                 group_address_setpoint_shift_state=None,
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
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address_operation_mode, (str, int)):
            group_address_operation_mode = Address(group_address_operation_mode)
        if isinstance(group_address_operation_mode_state, (str, int)):
            group_address_operation_mode_state = Address(group_address_operation_mode_state)
        if isinstance(group_address_operation_mode_protection, (str, int)):
            group_address_operation_mode_protection = Address(group_address_operation_mode_protection)
        if isinstance(group_address_operation_mode_night, (str, int)):
            group_address_operation_mode_night = Address(group_address_operation_mode_night)
        if isinstance(group_address_operation_mode_comfort, (str, int)):
            group_address_operation_mode_comfort = Address(group_address_operation_mode_comfort)
        if isinstance(group_address_controller_status, (str, int)):
            group_address_controller_status = Address(group_address_controller_status)
        if isinstance(group_address_controller_status_state, (str, int)):
            group_address_controller_status_state = Address(group_address_controller_status_state)

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
            after_update_cb=self.after_update)
        self.target_temperature = RemoteValueTemp(
            xknx,
            group_address_target_temperature,
            after_update_cb=self.after_update)
        self.setpoint = RemoteValueTemp(
            xknx,
            group_address_setpoint,
            after_update_cb=self.after_update)
        self.setpoint_shift = RemoteValue1Count(
            xknx,
            group_address_setpoint_shift,
            group_address_setpoint_shift_state,
            after_update_cb=self.after_update)

        self.setpoint_step = 0.5

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
        group_address_setpoint = \
            config.get('group_address_setpoint')
        group_address_setpoint_shift = \
            config.get('group_address_setpoint_shift')
        group_address_setpoint_shift_state = \
            config.get('group_address_setpoint_shift_state')
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
                   group_address_setpoint=group_address_setpoint,
                   group_address_setpoint_shift=group_address_setpoint_shift,
                   group_address_setpoint_shift_state=group_address_setpoint_shift_state,
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
            self.setpoint.has_group_address(group_address) or \
            self.setpoint_shift.has_group_address(group_address) or \
            self.group_address_operation_mode == group_address or \
            self.group_address_operation_mode_state == group_address or \
            self.group_address_operation_mode_protection == group_address or \
            self.group_address_operation_mode_night == group_address or \
            self.group_address_operation_mode_comfort == group_address or \
            self.group_address_controller_status == group_address or \
            self.group_address_controller_status_state == group_address

    @asyncio.coroutine
    def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            yield from self.after_update()

    @asyncio.coroutine
    def set_target_temperature_comfort(self, target_temperature_comfort):
        """Calculate setpoint shift and send it to  KNX bus."""
        if not self.setpoint.value:
            self.xknx.logger.warning("Setpoint temperature not know. Cant set target temperature")
            return
        if not self.setpoint_shift.initialized:
            self.xknx.logger.warning("Setpoint shift not know. Cant set target temperature")
            return
        setpoint_shift = int((target_temperature_comfort-self.setpoint.value)/self.setpoint_step)
        yield from self.setpoint_shift.set(setpoint_shift)

    @property
    def target_temperature_comfort(self):
        """Calculate target temperature out of basis setpoint and setpoint shift."""
        if self.setpoint.value is None or self.setpoint_shift.value is None:
            return None
        return self.setpoint.value + self.setpoint_step * (self.setpoint_shift.value)

    @asyncio.coroutine
    def set_operation_mode(self, operation_mode):
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if not self.supports_operation_mode:
            return
        if self.group_address_operation_mode is not None:
            yield from self.send(
                self.group_address_operation_mode,
                DPTArray(DPTHVACMode.to_knx(operation_mode)))
        if self.group_address_operation_mode_protection is not None:
            protection_mode = operation_mode == HVACOperationMode.FROST_PROTECTION
            yield from self.send(
                self.group_address_operation_mode_protection,
                DPTBinary(protection_mode))
        if self.group_address_operation_mode_night is not None:
            night_mode = operation_mode == HVACOperationMode.NIGHT
            yield from self.send(
                self.group_address_operation_mode_night,
                DPTBinary(night_mode))
        if self.group_address_operation_mode_comfort is not None:
            comfort_mode = operation_mode == HVACOperationMode.COMFORT
            yield from self.send(
                self.group_address_operation_mode_comfort,
                DPTBinary(comfort_mode))
        if self.group_address_controller_status is not None:
            yield from self.send(
                self.group_address_controller_status,
                DPTArray(DPTControllerStatus.to_knx(operation_mode)))
        yield from self._set_internal_operation_mode(operation_mode)

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

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        if self.supports_operation_mode and \
                telegram.group_address == self.group_address_operation_mode or \
                telegram.group_address == self.group_address_operation_mode_state:
            yield from self._process_operation_mode(telegram)
        elif self.supports_operation_mode and \
                telegram.group_address == self.group_address_controller_status or \
                telegram.group_address == self.group_address_controller_status_state:
            yield from self._process_controller_status(telegram)
        # Note: telegrams setting splitted up operation modes are not yet implemented

        yield from self.temperature.process(telegram)
        yield from self.target_temperature.process(telegram)
        yield from self.setpoint.process(telegram)
        yield from self.setpoint_shift.process(telegram)

    @asyncio.coroutine
    def _process_operation_mode(self, telegram):
        """Process incoming telegram for operation mode."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()
        operation_mode = DPTHVACMode.from_knx(telegram.payload.value)
        yield from self._set_internal_operation_mode(operation_mode)

    @asyncio.coroutine
    def _process_controller_status(self, telegram):
        """Process incoming telegram for controller status."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()
        operation_mode = DPTControllerStatus.from_knx(telegram.payload.value)
        yield from self._set_internal_operation_mode(operation_mode)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.temperature.state_addresses())
        state_addresses.extend(self.target_temperature.state_addresses())
        state_addresses.extend(self.setpoint.state_addresses())
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
            'setpoint="{3}" ' \
            'setpoint_shift="{4}" ' \
            'group_address_operation_mode="{5}" ' \
            'group_address_operation_mode_state="{6}" ' \
            'group_address_controller_status="{7}" ' \
            'group_address_controller_status_state="{8}" ' \
            '/>' \
            .format(
                self.name,
                self.temperature.group_addr_str(),
                self.target_temperature.group_addr_str(),
                self.setpoint.group_addr_str(),
                self.setpoint_shift.group_addr_str(),
                self.group_address_operation_mode,
                self.group_address_operation_mode_state,
                self.group_address_controller_status,
                self.group_address_controller_status_state)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
