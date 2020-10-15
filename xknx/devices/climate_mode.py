"""
Module for managing operation and controller modes.

Operation modes can be 'auto', 'comfort', 'standby', 'economy', 'protection' and use either a binary DPT or DPT 20.102.
Controller modes use DPT 20.105.
"""
from itertools import chain

from xknx.dpt import HVACControllerMode, HVACOperationMode
from xknx.exceptions import DeviceIllegalValue
from xknx.remote_value import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueClimateMode,
)

from .device import Device


class ClimateMode(Device):
    """Class for managing the climate mode."""

    # pylint: disable=invalid-name,too-many-instance-attributes

    def __init__(
        self,
        xknx,
        name,
        group_address_operation_mode=None,
        group_address_operation_mode_state=None,
        group_address_operation_mode_protection=None,
        group_address_operation_mode_night=None,
        group_address_operation_mode_comfort=None,
        group_address_operation_mode_standby=None,
        group_address_controller_status=None,
        group_address_controller_status_state=None,
        group_address_controller_mode=None,
        group_address_controller_mode_state=None,
        group_address_heat_cool=None,
        group_address_heat_cool_state=None,
        operation_modes=None,
        controller_modes=None,
        device_updated_cb=None,
    ):
        """Initialize ClimateMode class."""
        # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        super().__init__(xknx, name, device_updated_cb)

        self.remote_value_operation_mode = RemoteValueClimateMode(
            xknx,
            group_address=group_address_operation_mode,
            group_address_state=group_address_operation_mode_state,
            sync_state=True,
            device_name=name,
            feature_name="Operation mode",
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE,
            after_update_cb=None,
        )
        self.remote_value_controller_mode = RemoteValueClimateMode(
            xknx,
            group_address=group_address_controller_mode,
            group_address_state=group_address_controller_mode_state,
            sync_state=True,
            device_name=name,
            feature_name="Controller mode",
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_CONTR_MODE,
            after_update_cb=None,
        )
        self.remote_value_controller_status = RemoteValueClimateMode(
            xknx,
            group_address=group_address_controller_status,
            group_address_state=group_address_controller_status_state,
            sync_state=True,
            device_name=name,
            feature_name="Controller status",
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.CONTROLLER_STATUS,
            after_update_cb=None,
        )

        self.remote_value_operation_mode_comfort = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_comfort,
            group_address_state=group_address_operation_mode_comfort,
            sync_state=True,
            device_name=name,
            feature_name="Operation mode Comfort",
            operation_mode=HVACOperationMode.COMFORT,
            after_update_cb=None,
        )
        self.remote_value_operation_mode_standby = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_standby,
            group_address_state=group_address_operation_mode_standby,
            sync_state=True,
            device_name=name,
            feature_name="Operation mode Standby",
            operation_mode=HVACOperationMode.STANDBY,
            after_update_cb=None,
        )
        self.remote_value_operation_mode_night = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_night,
            group_address_state=group_address_operation_mode_night,
            sync_state=True,
            device_name=name,
            feature_name="Operation mode Night",
            operation_mode=HVACOperationMode.NIGHT,
            after_update_cb=None,
        )
        self.remote_value_operation_mode_protection = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_protection,
            group_address_state=group_address_operation_mode_protection,
            sync_state=True,
            device_name=name,
            feature_name="Operation mode Protection",
            operation_mode=HVACOperationMode.FROST_PROTECTION,
            after_update_cb=None,
        )
        self.remote_value_heat_cool = RemoteValueBinaryHeatCool(
            xknx,
            group_address=group_address_heat_cool,
            group_address_state=group_address_heat_cool_state,
            sync_state=True,
            device_name=name,
            feature_name="Heat/Cool",
            controller_mode=HVACControllerMode.HEAT,
            after_update_cb=None,
        )

        self.operation_mode = HVACOperationMode.STANDBY
        self.controller_mode = HVACControllerMode.HEAT

        self._operation_modes = []
        if operation_modes is None:
            self._operation_modes = self.gather_operation_modes()
        else:
            for mode in operation_modes:
                if isinstance(mode, str):
                    self._operation_modes.append(HVACOperationMode(mode))
                elif isinstance(mode, HVACOperationMode):
                    self._operation_modes.append(mode)

        self._controller_modes = []
        if controller_modes is None:
            self._controller_modes = self.gather_controller_modes()
        else:
            for mode in controller_modes:
                if isinstance(mode, str):
                    self._controller_modes.append(HVACControllerMode(mode))
                elif isinstance(mode, HVACControllerMode):
                    self._controller_modes.append(mode)

        self.supports_operation_mode = any(
            operation_mode.initialized
            for operation_mode in self._iter_byte_operation_modes()
        ) or any(
            operation_mode.initialized
            for operation_mode in self._iter_binary_operation_modes()
        )
        self.supports_controller_mode = any(
            operation_mode.initialized
            for operation_mode in self._iter_controller_remote_values()
        )

        self._use_binary_operation_modes = any(
            operation_mode.initialized
            for operation_mode in self._iter_binary_operation_modes()
        )

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        # pylint: disable=too-many-locals
        group_address_operation_mode = config.get("group_address_operation_mode")
        group_address_operation_mode_state = config.get(
            "group_address_operation_mode_state"
        )
        group_address_operation_mode_protection = config.get(
            "group_address_operation_mode_protection"
        )
        group_address_operation_mode_night = config.get(
            "group_address_operation_mode_night"
        )
        group_address_operation_mode_comfort = config.get(
            "group_address_operation_mode_comfort"
        )
        group_address_operation_mode_standby = config.get(
            "group_address_operation_mode_standby"
        )
        group_address_controller_status = config.get("group_address_controller_status")
        group_address_controller_status_state = config.get(
            "group_address_controller_status_state"
        )
        group_address_controller_mode = config.get("group_address_controller_mode")
        group_address_controller_mode_state = config.get(
            "group_address_controller_mode_state"
        )
        group_address_heat_cool = config.get("group_address_heat_cool")
        group_address_heat_cool_state = config.get("group_address_heat_cool_state")

        return cls(
            xknx,
            name,
            group_address_operation_mode=group_address_operation_mode,
            group_address_operation_mode_state=group_address_operation_mode_state,
            group_address_operation_mode_protection=group_address_operation_mode_protection,
            group_address_operation_mode_night=group_address_operation_mode_night,
            group_address_operation_mode_comfort=group_address_operation_mode_comfort,
            group_address_operation_mode_standby=group_address_operation_mode_standby,
            group_address_controller_status=group_address_controller_status,
            group_address_controller_status_state=group_address_controller_status_state,
            group_address_controller_mode=group_address_controller_mode,
            group_address_controller_mode_state=group_address_controller_mode_state,
            group_address_heat_cool=group_address_heat_cool,
            group_address_heat_cool_state=group_address_heat_cool_state,
        )

    def _iter_remote_values(self):
        """Iterate climate mode RemoteValue classes."""
        return chain(
            self._iter_byte_operation_modes(),
            self._iter_controller_remote_values(),
            self._iter_binary_operation_modes(),
        )

    def _iter_byte_operation_modes(self):
        """Iterate normal DPT 20.102 operation mode remote values."""
        yield from (
            self.remote_value_operation_mode,
            self.remote_value_controller_status,
        )

    def _iter_controller_remote_values(self):
        """Iterate DPT 20.105 controller remote values."""
        yield from (
            self.remote_value_controller_mode,
            self.remote_value_heat_cool,
        )

    def _iter_binary_operation_modes(self):
        """Iterate DPT 1 binary operation modes."""
        yield from (
            self.remote_value_operation_mode_comfort,
            self.remote_value_operation_mode_night,
            self.remote_value_operation_mode_protection,
            self.remote_value_operation_mode_standby,
        )

    async def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            await self.after_update()

    async def _set_internal_controller_mode(self, controller_mode):
        """Set internal value of controller mode. Call hooks if controller mode was changed."""
        if controller_mode != self.controller_mode:
            self.controller_mode = controller_mode
            await self.after_update()

    async def set_operation_mode(self, operation_mode):
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if (
            not self.supports_operation_mode
            or operation_mode not in self._operation_modes
        ):
            raise DeviceIllegalValue(
                "operation (preset) mode not supported", operation_mode
            )

        for rv in chain(
            self._iter_byte_operation_modes(), self._iter_binary_operation_modes()
        ):
            if rv.writable and operation_mode in rv.supported_operation_modes():
                await rv.set(operation_mode)

        await self._set_internal_operation_mode(operation_mode)

    async def set_controller_mode(self, controller_mode):
        """Set the controller mode of a thermostat. Send new controller mode to the bus and update internal state."""
        if (
            not self.supports_controller_mode
            or controller_mode not in self._controller_modes
        ):
            raise DeviceIllegalValue(
                "controller (HVAC) mode not supported", controller_mode
            )

        for rv in self._iter_controller_remote_values():
            if rv.writable and controller_mode in rv.supported_operation_modes():
                await rv.set(controller_mode)

        await self._set_internal_controller_mode(controller_mode)

    @property
    def operation_modes(self):
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []
        return self._operation_modes

    @property
    def controller_modes(self):
        """Return all configured controller modes."""
        if not self.supports_controller_mode:
            return []
        return self._controller_modes

    def gather_operation_modes(self):
        """Gather operation modes from RemoteValues."""
        operation_modes = []
        for rv in chain(
            self._iter_binary_operation_modes(), self._iter_byte_operation_modes()
        ):
            if rv.writable:
                operation_modes.extend(rv.supported_operation_modes())

        # remove duplicates
        return list(set(operation_modes))

    def gather_controller_modes(self):
        """Gather controller modes from RemoteValues."""
        operation_modes = []
        for rv in self._iter_controller_remote_values():
            if rv.writable:
                operation_modes.extend(rv.supported_operation_modes())

        # remove duplicates
        return list(set(operation_modes))

    async def process_group_write(self, telegram):
        """Process incoming and outgoing GROUP WRITE telegram."""
        if self.supports_operation_mode:
            for rv in self._iter_remote_values():
                if await rv.process(telegram):
                    #  ignore inactive RemoteValueBinaryOperationMode
                    if rv.value:
                        await self._set_internal_operation_mode(rv.value)
                        return

        if self.supports_controller_mode:
            for rv in self._iter_controller_remote_values():
                if await rv.process(telegram):
                    await self._set_internal_controller_mode(rv.value)
                    return

    def __str__(self):
        """Return object as readable string."""
        return (
            '<ClimateMode name="{}" '
            'operation_mode="{}" '
            'controller_mode="{}" '
            'controller_status="{}" '
            "/>".format(
                self.name,
                self.remote_value_operation_mode.group_addr_str(),
                self.remote_value_controller_mode.group_addr_str(),
                self.remote_value_controller_status.group_addr_str(),
            )
        )
