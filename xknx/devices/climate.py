"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
import time
import datetime
import asyncio
from xknx.knx import Address, DPTBinary, DPTArray, DPTTemperature, \
    HVACOperationMode, DPTControllerStatus, DPTHVACMode
from xknx.exceptions import CouldNotParseTelegram
from .device import Device


class Climate(Device):
    """Class for managing the climate."""

    # pylint: disable=too-many-instance-attributes,invalid-name

    def __init__(self,
                 xknx,
                 name,
                 group_address_temperature=None,
                 group_address_target_temperature=None,
                 group_address_setpoint=None,
                 group_address_operation_mode=None,
                 group_address_operation_mode_state=None,
                 group_address_operation_mode_protection=None,
                 group_address_operation_mode_night=None,
                 group_address_operation_mode_comfort=None,
                 group_address_controller_status=None,
                 group_address_controller_status_state=None,
                 device_updated_cb=None):
        """Initialize Climate class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address_temperature, (str, int)):
            group_address_temperature = Address(group_address_temperature)
        if isinstance(group_address_target_temperature, (str, int)):
            group_address_target_temperature = Address(group_address_target_temperature)
        if isinstance(group_address_setpoint, (str, int)):
            group_address_setpoint = Address(group_address_setpoint)
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

        self.group_address_temperature = group_address_temperature
        self.group_address_target_temperature = group_address_target_temperature
        self.group_address_setpoint = group_address_setpoint
        self.group_address_operation_mode = group_address_operation_mode
        self.group_address_operation_mode_state = group_address_operation_mode_state
        self.group_address_operation_mode_protection = group_address_operation_mode_protection
        self.group_address_operation_mode_night = group_address_operation_mode_night
        self.group_address_operation_mode_comfort = group_address_operation_mode_comfort
        self.group_address_controller_status = group_address_controller_status
        self.group_address_controller_status_state = group_address_controller_status_state

        self.last_set = None
        self.temperature = None
        self.target_temperature = None
        self.setpoint = None
        self.operation_mode = HVACOperationMode.STANDBY

        self.supports_temperature = \
            group_address_temperature is not None
        self.supports_target_temperature = \
            group_address_target_temperature is not None
        self.supports_setpoint = \
            group_address_setpoint is not None
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
        group_address_temperature = \
            config.get('group_address_temperature')
        group_address_target_temperature = \
            config.get('group_address_target_temperature')
        group_address_setpoint = \
            config.get('group_address_setpoint')
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
                   group_address_operation_mode=group_address_operation_mode,
                   group_address_operation_mode_state=group_address_operation_mode_state,
                   group_address_operation_mode_protection=group_address_operation_mode_protection,
                   group_address_operation_mode_night=group_address_operation_mode_night,
                   group_address_operation_mode_comfort=group_address_operation_mode_comfort,
                   group_address_controller_status=group_address_controller_status,
                   group_address_controller_status_state=group_address_controller_status_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.group_address_temperature == group_address or \
            self.group_address_target_temperature == group_address or \
            self.group_address_setpoint == group_address or \
            self.group_address_operation_mode == group_address or \
            self.group_address_operation_mode_state == group_address or \
            self.group_address_operation_mode_protection == group_address or \
            self.group_address_operation_mode_night == group_address or \
            self.group_address_operation_mode_comfort == group_address or \
            self.group_address_controller_status == group_address or \
            self.group_address_controller_status_state == group_address

    @asyncio.coroutine
    def _set_internal_setpoint(self, setpoint):
        """Set internal value of setpoint. Call hooks if setpoint was changed."""
        if setpoint != self.setpoint:
            self.setpoint = setpoint
            yield from self.after_update()

    @asyncio.coroutine
    def _set_internal_temperature(self, temperature):
        """Set internal value of temperature. Call hooks if setpoint was changed."""
        if temperature != self.temperature:
            self.temperature = temperature
            yield from self.after_update()

    @asyncio.coroutine
    def _set_internal_target_temperature(self, target_temperature):
        """Set internal value of target temperature. Call hooks if setpoint was changed."""
        if target_temperature != self.target_temperature:
            self.target_temperature = target_temperature
            yield from self.after_update()

    @asyncio.coroutine
    def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operatio nmode. Call hooks if setpoint was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            yield from self.after_update()

    @asyncio.coroutine
    def set_setpoint(self, setpoint):
        """Send setpoint to KNX bus."""
        if not self.supports_setpoint:
            return
        yield from self.send(
            self.group_address_setpoint,
            DPTArray(DPTTemperature().to_knx(setpoint)))
        yield from self._set_internal_setpoint(setpoint)

    @asyncio.coroutine
    def set_target_temperature(self, target_temperature):
        """Calculate setpoint-delta and setpoint and send it to  KNX bus."""
        if not self.setpoint:
            self.xknx.logger.warning(
                "Could not set new target temperature "
                "- setpoint temperature not determined")
            return
        if not self.target_temperature:
            self.xknx.logger.warning(
                "Could not set new target temperature "
                "- old target temperature not determined")
            return
        setpoint_delta = self.setpoint - self.target_temperature
        new_setpoint = target_temperature + setpoint_delta
        yield from self.set_setpoint(new_setpoint)

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
            return list(HVACOperationMode)

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
        if telegram.group_address == self.group_address_temperature and \
                self.supports_temperature:
            yield from self._process_temperature(telegram)
        if telegram.group_address == self.group_address_target_temperature and \
                self.supports_target_temperature:
            yield from self._process_target_temperature(telegram)
        elif telegram.group_address == self.group_address_setpoint and \
                self.supports_setpoint:
            yield from self._process_setpoint(telegram)
        elif self.supports_operation_mode and \
                telegram.group_address == self.group_address_operation_mode or \
                telegram.group_address == self.group_address_operation_mode_state:
            yield from self._process_operation_mode(telegram)
        elif self.supports_operation_mode and \
                telegram.group_address == self.group_address_controller_status or \
                telegram.group_address == self.group_address_controller_status_state:
            yield from self._process_controller_status(telegram)
        # Note: telegrams setting splitted up operation modes are not yet implemented

    @asyncio.coroutine
    def _process_temperature(self, telegram):
        """Process incoming telegram for temperature."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()
        temperature = DPTTemperature().from_knx(
            (telegram.payload.value[0],
             telegram.payload.value[1]))
        self.last_set = time.time()
        yield from self._set_internal_temperature(temperature)

    @asyncio.coroutine
    def _process_target_temperature(self, telegram):
        """Process incoming telegram for target temperature."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()
        target_temperature = DPTTemperature().from_knx(
            (telegram.payload.value[0],
             telegram.payload.value[1]))
        self.last_set = time.time()
        yield from self._set_internal_target_temperature(target_temperature)

    @asyncio.coroutine
    def _process_setpoint(self, telegram):
        """Process incoming telegram for setpoint."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()
        setpoint = DPTTemperature().from_knx(
            (telegram.payload.value[0],
             telegram.payload.value[1]))
        yield from self._set_internal_setpoint(setpoint)

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
        if self.supports_temperature:
            state_addresses.append(self.group_address_temperature)
        if self.supports_target_temperature:
            state_addresses.append(self.group_address_target_temperature)
        if self.supports_setpoint:
            state_addresses.append(self.group_address_setpoint)
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
        last_set_formatted = \
            datetime.datetime.fromtimestamp(self.last_set).strftime('%Y-%m-%d %H:%M:%S') \
            if self.last_set else None
        return '<Climate name="{0}" ' \
            'group_address_temperature="{1}"  ' \
            'group_address_target_temperature="{2}"  ' \
            'group_address_setpoint="{3}" ' \
            'group_address_operation_mode="{4}" ' \
            'group_address_operation_mode_state="{5}" ' \
            'group_address_controller_status="{6}" ' \
            'group_address_controller_status_state="{7}" ' \
            'temperature="{8}" ' \
            'last_set="{9}" />' \
            .format(
                self.name,
                self.group_address_temperature,
                self.group_address_target_temperature,
                self.group_address_setpoint,
                self.group_address_operation_mode,
                self.group_address_operation_mode_state,
                self.group_address_controller_status,
                self.group_address_controller_status_state,
                self.temperature,
                last_set_formatted)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
