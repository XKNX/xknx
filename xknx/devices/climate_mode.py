"""
Module for managing the climate mode.

Climate modes can be 'auto', 'comfort', 'standby', 'economy' or 'protection'.
"""
from xknx.dpt import HVACOperationMode
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
            operation_mode=HVACOperationMode.HEAT,
            after_update_cb=None,
        )

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

        self.supports_operation_mode = (
            group_address_operation_mode is not None
            or group_address_operation_mode_state is not None
            or group_address_operation_mode_protection is not None
            or group_address_operation_mode_night is not None
            or group_address_operation_mode_comfort is not None
            or group_address_operation_mode_standby is not None
            or group_address_controller_status is not None
            or group_address_controller_status_state is not None
            or group_address_controller_mode is not None
            or group_address_controller_mode_state is not None
            or group_address_heat_cool is not None
            or group_address_heat_cool_state is not None
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
        yield from (
            self.remote_value_controller_mode,
            self.remote_value_controller_status,
            self.remote_value_operation_mode,
            self.remote_value_operation_mode_comfort,
            self.remote_value_operation_mode_night,
            self.remote_value_operation_mode_protection,
            self.remote_value_operation_mode_standby,
            self.remote_value_heat_cool,
        )

    async def _set_internal_operation_mode(self, operation_mode):
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            await self.after_update()

    async def set_operation_mode(self, operation_mode):
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if (
            not self.supports_operation_mode
            or operation_mode not in self.operation_modes_
        ):
            raise DeviceIllegalValue("operation mode not supported", operation_mode)

        for rv in self._iter_remote_values():
            if rv.writable and operation_mode in rv.supported_operation_modes():
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
        for rv in self._iter_remote_values():
            if rv.writable:
                operation_modes.extend(rv.supported_operation_modes())
        # remove duplicates
        return list(set(operation_modes))

    async def process_group_write(self, telegram):
        """Process incoming and outgoing GROUP WRITE telegram."""
        if self.supports_operation_mode:
            processed = False
            for rv in self._iter_remote_values():
                if await rv.process(telegram):
                    # don't set when binary climate mode rv is False
                    if rv.value:
                        await self._set_internal_operation_mode(rv.value)
                        return
                    processed = True
            # if no operation mode has been set and all binary operation modes are False
            if processed:
                await self._set_internal_operation_mode(HVACOperationMode.STANDBY)

    async def sync(self, wait_for_result=False):
        """Read states of device from KNX bus."""
        if self.supports_operation_mode:
            for rv in self._iter_remote_values():
                await rv.read_state(wait_for_result=wait_for_result)

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
