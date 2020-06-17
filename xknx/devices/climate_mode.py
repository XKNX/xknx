"""
Module for managing the climate mode.

Climate modes can be 'auto', 'comfort', 'standby', 'economy' or 'protection'.
"""
from xknx.dpt import HVACOperationMode
from xknx.exceptions import DeviceIllegalValue
from xknx.remote_value import (
    RemoteValueClimateBinaryMode, RemoteValueClimateMode)

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

        self.remote_value_operation_mode_comfort = RemoteValueClimateBinaryMode(
            xknx,
            group_address=group_address_operation_mode_comfort,
            group_address_state=group_address_operation_mode_comfort,
            sync_state=True,
            device_name=name,
            operation_mode=HVACOperationMode.COMFORT,
            after_update_cb=None)
        self.remote_value_operation_mode_night = RemoteValueClimateBinaryMode(
            xknx,
            group_address=group_address_operation_mode_night,
            group_address_state=group_address_operation_mode_night,
            sync_state=True,
            device_name=name,
            operation_mode=HVACOperationMode.NIGHT,
            after_update_cb=None)
        self.remote_value_operation_mode_protection = RemoteValueClimateBinaryMode(
            xknx,
            group_address=group_address_operation_mode_protection,
            group_address_state=group_address_operation_mode_protection,
            sync_state=True,
            device_name=name,
            operation_mode=HVACOperationMode.FROST_PROTECTION,
            after_update_cb=None)

        self.operation_mode = HVACOperationMode.STANDBY

        self.operation_modes_ = []
        if operation_modes is None:
            self.operation_modes_ = self.gather_operation_modes()
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
        for rv in self.__iter_remote_values():
            if rv.has_group_address(group_address):
                return True
        return False

    def __iter_remote_values(self):
        """Iterate climate mode RemoteValue classes."""
        yield from self.__iter_remote_values_climate_mode()
        yield from self.__iter_remote_values_climate_binary_mode()

    def __iter_remote_values_climate_mode(self):
        """Iterate climate mode RemoteValue classes."""
        yield from (self.remote_value_controller_mode,
                    self.remote_value_controller_status,
                    self.remote_value_operation_mode)

    def __iter_remote_values_climate_binary_mode(self):
        """Iterate climate mode RemoteValue classes."""
        yield from (self.remote_value_operation_mode_comfort,
                    self.remote_value_operation_mode_night,
                    self.remote_value_operation_mode_protection)

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

        for rv in self.__iter_remote_values_climate_mode():
            if rv.writable and \
                    operation_mode in rv.supported_operation_modes():
                await rv.set(operation_mode)

        for rv in self.__iter_remote_values_climate_binary_mode():
            if rv.writable:
                # foreign operation modes will set the RemoteValue to False
                await rv.set(operation_mode)

        await self._set_internal_operation_mode(operation_mode)

    @property
    def operation_modes(self):
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []
        return self.operation_modes_

    def gather_operation_modes(self):
        """Gather operation modes from RemoteValues."""
        operation_modes = []
        for rv in self.__iter_remote_values():
            if rv.writable:
                operation_modes.extend(rv.supported_operation_modes())
        # remove duplicates
        return list(set(operation_modes))

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if self.supports_operation_mode:
            for rv in self.__iter_remote_values():
                if await rv.process(telegram):
                    # don't set when binary climate mode rv is False
                    if rv.value:
                        await self._set_internal_operation_mode(rv.value)
                        return
            # if no operation mode has been set and all binary operation modes are False
            await self._set_internal_operation_mode(HVACOperationMode.STANDBY)

    #TODO: state_updater
    async def sync(self):
        if self.supports_operation_mode:
            for rv in self.__iter_remote_values():
                rv.read_state()

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
