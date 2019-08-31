"""
Module for managing the climate mode.

Climate modes can be 'auto', 'comfort', 'standby', 'economy' or 'protection'.
"""
from xknx.dpt import (
    DPTArray, DPTBinary, DPTControllerStatus, DPTHVACContrMode, DPTHVACMode,
    HVACOperationMode)
from xknx.exceptions import CouldNotParseTelegram, DeviceIllegalValue
from xknx.telegram import GroupAddress

from .device import Device


class ClimateMode(Device):
    """Class for managing the climate mode."""

    # pylint: disable=invalid-name,too-many-instance-attributes

    def __init__(self,
                 xknx,
                 name,
                 group_address_operation_mode=None,
                 group_address_operation_mode_state=None,
                 group_address_operation_mode_protection=None,
                 group_address_operation_mode_night=None,
                 group_address_operation_mode_comfort=None,
                 group_address_controller_status=None,
                 group_address_controller_status_state=None,
                 group_address_controller_mode=None,
                 group_address_controller_mode_state=None,
                 operation_modes=None,
                 device_updated_cb=None):
        """Initialize ClimateMode class."""
        # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        super().__init__(xknx, name, device_updated_cb)
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
        if isinstance(group_address_controller_mode, (str, int)):
            group_address_controller_mode = GroupAddress(group_address_controller_mode)
        if isinstance(group_address_controller_mode_state, (str, int)):
            group_address_controller_mode_state = GroupAddress(group_address_controller_mode_state)

        self.group_address_operation_mode = group_address_operation_mode
        self.group_address_operation_mode_state = group_address_operation_mode_state
        self.group_address_operation_mode_protection = group_address_operation_mode_protection
        self.group_address_operation_mode_night = group_address_operation_mode_night
        self.group_address_operation_mode_comfort = group_address_operation_mode_comfort
        self.group_address_controller_status = group_address_controller_status
        self.group_address_controller_status_state = group_address_controller_status_state
        self.group_address_controller_mode = group_address_controller_mode
        self.group_address_controller_mode_state = group_address_controller_mode_state

        self.operation_mode = HVACOperationMode.STANDBY

        self.operation_modes_ = []
        if operation_modes is None:
            self.operation_modes_ = self.guess_operation_modes()
        else:
            for mode in operation_modes:
                if isinstance(mode, str):
                    self.operation_modes_.append(HVACOperationMode[mode])
                elif isinstance(mode, HVACOperationMode):
                    self.operation_modes_.append(mode)

        self.supports_operation_mode = \
            group_address_operation_mode is not None or \
            group_address_operation_mode_state is not None or \
            group_address_operation_mode_protection is not None or \
            group_address_operation_mode_night is not None or \
            group_address_operation_mode_comfort is not None or \
            group_address_controller_status is not None or \
            group_address_controller_status_state is not None or \
            group_address_controller_mode is not None or \
            group_address_controller_mode_state is not None

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        # pylint: disable=too-many-locals
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
        group_address_controller_mode = \
            config.get('group_address_controller_mode')
        group_address_controller_mode_state = \
            config.get('group_address_controller_mode_state')

        return cls(xknx,
                   name,
                   group_address_operation_mode=group_address_operation_mode,
                   group_address_operation_mode_state=group_address_operation_mode_state,
                   group_address_operation_mode_protection=group_address_operation_mode_protection,
                   group_address_operation_mode_night=group_address_operation_mode_night,
                   group_address_operation_mode_comfort=group_address_operation_mode_comfort,
                   group_address_controller_status=group_address_controller_status,
                   group_address_controller_status_state=group_address_controller_status_state,
                   group_address_controller_mode=group_address_controller_mode,
                   group_address_controller_mode_state=group_address_controller_mode_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return group_address in \
            [self.group_address_operation_mode,
             self.group_address_operation_mode_state,
             self.group_address_operation_mode_protection,
             self.group_address_operation_mode_night,
             self.group_address_operation_mode_comfort,
             self.group_address_controller_status,
             self.group_address_controller_status_state,
             self.group_address_controller_mode,
             self.group_address_controller_mode_state]

    async def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            await self.after_update()

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
        if self.group_address_controller_mode is not None:
            await self.send(
                self.group_address_controller_mode,
                DPTArray(DPTHVACContrMode.to_knx(operation_mode)))
        await self._set_internal_operation_mode(operation_mode)

    @property
    def operation_modes(self):
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []
        return self.operation_modes_

    def guess_operation_modes(self):
        """Guess operation modes from group addresses."""
        # All operation modes supported
        if self.group_address_operation_mode is not None:
            return [HVACOperationMode.AUTO, HVACOperationMode.COMFORT,
                    HVACOperationMode.STANDBY, HVACOperationMode.NIGHT,
                    HVACOperationMode.FROST_PROTECTION]
        if self.group_address_controller_status is not None:
            return [HVACOperationMode.COMFORT, HVACOperationMode.STANDBY,
                    HVACOperationMode.NIGHT, HVACOperationMode.FROST_PROTECTION]
        if self.group_address_controller_mode is not None:
            return [HVACOperationMode.STANDBY, HVACOperationMode.AUTO, HVACOperationMode.HEAT,
                    HVACOperationMode.COOL, HVACOperationMode.FAN_ONLY, HVACOperationMode.DRY]

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
                telegram.group_address == self.group_address_controller_mode or \
                telegram.group_address == self.group_address_controller_mode_state:
            await self._process_controller_mode(telegram)
        elif self.supports_operation_mode and \
                telegram.group_address == self.group_address_controller_status or \
                telegram.group_address == self.group_address_controller_status_state:
            await self._process_controller_status(telegram)
        # Note: telegrams setting splitted up operation modes are not yet implemented

    async def _process_operation_mode(self, telegram):
        """Process incoming telegram for operation mode."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram("invalid payload", payload=telegram.payload, device_name=self.name)
        operation_mode = DPTHVACMode.from_knx(telegram.payload.value)
        await self._set_internal_operation_mode(operation_mode)

    async def _process_controller_mode(self, telegram):
        """Process incoming telegram for controller mode."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram("invalid payload", payload=telegram.payload, device_name=self.name)
        operation_mode = DPTHVACContrMode.from_knx(telegram.payload.value)
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

        if self.supports_operation_mode:
            if self.group_address_operation_mode_state:
                state_addresses.append(self.group_address_operation_mode_state)
            if self.group_address_controller_status_state:
                state_addresses.append(self.group_address_controller_status_state)
            if self.group_address_controller_mode_state:
                state_addresses.append(self.group_address_controller_mode_state)
            # Note: telegrams setting splitted up operation modes are not yet implemented
        return state_addresses

    def __str__(self):
        """Return object as readable string."""
        return '<ClimateMode name="{0}" ' \
            'group_address_operation_mode="{1}" ' \
            'group_address_operation_mode_state="{2}" ' \
            'group_address_controller_status="{3}" ' \
            'group_address_controller_status_state="{4}" ' \
            'group_address_controller_mode="{5}" ' \
            'group_address_controller_mode_state="{6}" ' \
            '/>' \
            .format(
                self.name,
                self.group_address_operation_mode.__repr__(),
                self.group_address_operation_mode_state.__repr__(),
                self.group_address_controller_status.__repr__(),
                self.group_address_controller_status_state.__repr__(),
                self.group_address_controller_mode.__repr__(),
                self.group_address_controller_mode_state.__repr__())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
