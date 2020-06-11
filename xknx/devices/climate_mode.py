"""
Module for managing the climate mode.

Climate modes can be 'auto', 'comfort', 'standby', 'economy' or 'protection'.
"""
from xknx.dpt import DPTBinary, HVACOperationMode
from xknx.exceptions import DeviceIllegalValue
from xknx.remote_value import RemoteValueClimateMode
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

        self.group_address_operation_mode_protection = group_address_operation_mode_protection
        self.group_address_operation_mode_night = group_address_operation_mode_night
        self.group_address_operation_mode_comfort = group_address_operation_mode_comfort

        self.remote_value_operation_mode = RemoteValueClimateMode(
            xknx,
            group_address=group_address_operation_mode,
            group_address_state=group_address_operation_mode_state,
            sync_state=True,
            device_name=name,
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE,
            after_update_cb=None)
        self.remote_value_controller_mode = RemoteValueClimateMode(
            xknx,
            group_address=group_address_controller_mode,
            group_address_state=group_address_controller_mode_state,
            sync_state=True,
            device_name=name,
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_CONTR_MODE,
            after_update_cb=None)
        self.remote_value_controller_status = RemoteValueClimateMode(
            xknx,
            group_address=group_address_controller_status,
            group_address_state=group_address_controller_status_state,
            sync_state=True,
            device_name=name,
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.CONTROLLER_STATUS,
            after_update_cb=None)

        self.operation_mode = HVACOperationMode.STANDBY

        self.operation_modes_ = []
        if operation_modes is None:
            self.operation_modes_ = self.guess_operation_modes()
        else:
            for mode in operation_modes:
                if isinstance(mode, str):
                    self.operation_modes_.append(HVACOperationMode(mode))
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

    @ classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        # pylint: disable=too-many-locals
        group_address_operation_mode = config.get('group_address_operation_mode')
        group_address_operation_mode_state = config.get('group_address_operation_mode_state')
        group_address_operation_mode_protection = config.get('group_address_operation_mode_protection')
        group_address_operation_mode_night = config.get('group_address_operation_mode_night')
        group_address_operation_mode_comfort = config.get('group_address_operation_mode_comfort')
        group_address_controller_status = config.get('group_address_controller_status')
        group_address_controller_status_state = config.get('group_address_controller_status_state')
        group_address_controller_mode = config.get('group_address_controller_mode')
        group_address_controller_mode_state = config.get('group_address_controller_mode_state')

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
        for rv in self._climate_mode_remote_values():
            if rv.has_group_address(group_address):
                return True
        return group_address in (
            self.group_address_operation_mode_protection,
            self.group_address_operation_mode_night,
            self.group_address_operation_mode_comfort)

    def _climate_mode_remote_values(self):
        """Iterate climate mode RemoteValue classes."""
        yield from (self.remote_value_controller_mode,
                    self.remote_value_controller_status,
                    self.remote_value_operation_mode)

    async def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            await self.after_update()

    async def set_operation_mode(self, operation_mode):
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if not self.supports_operation_mode or \
                operation_mode not in self.operation_modes_:
            raise DeviceIllegalValue("operation mode not supported", operation_mode)

        for rv in self._climate_mode_remote_values():
            if rv.writable and \
                    operation_mode in rv.supported_operation_modes():
                await rv.set(operation_mode)

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

        await self._set_internal_operation_mode(operation_mode)

    @property
    def operation_modes(self):
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []
        return self.operation_modes_

    def guess_operation_modes(self):
        """Guess operation modes from group addresses."""
        operation_modes = []
        for rv in self._climate_mode_remote_values():
            if rv.writable:
                operation_modes.extend(rv.supported_operation_modes())
        if not operation_modes:
            operation_modes.append(HVACOperationMode.STANDBY)
        # Operation modes only supported partially
        if self.group_address_operation_mode_comfort:
            operation_modes.append(HVACOperationMode.COMFORT)
        if self.group_address_operation_mode_night:
            operation_modes.append(HVACOperationMode.NIGHT)
        if self.group_address_operation_mode_protection:
            operation_modes.append(HVACOperationMode.FROST_PROTECTION)
        # remove duplicates
        return list(set(operation_modes))

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if self.supports_operation_mode:
            for rv in self._climate_mode_remote_values():
                if await rv.process(telegram):
                    await self._set_internal_operation_mode(rv.value)
        # Note: telegrams setting splitted up operation modes are not yet implemented

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []

        if self.supports_operation_mode:
            for rv in self._climate_mode_remote_values():
                state_addresses.extend(rv.state_addresses())
            # Note: telegrams setting splitted up operation modes are not yet implemented
        return state_addresses

    def __str__(self):
        """Return object as readable string."""
        return '<ClimateMode name="{0}" ' \
            'operation_mode="{1}" ' \
            'controller_mode="{2}" ' \
            'controller_status="{3}" ' \
            '/>' \
            .format(
                self.name,
                self.remote_value_operation_mode.group_addr_str(),
                self.remote_value_controller_mode.group_addr_str(),
                self.remote_value_controller_status.group_addr_str(),)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
