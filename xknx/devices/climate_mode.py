"""
Module for managing operation and controller modes.

Operation modes can be 'auto', 'comfort', 'standby', 'economy', 'protection' and use either a binary DPT or DPT 20.102.
Controller modes use DPT 20.105.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from xknx.dpt.dpt_1 import HeatCool
from xknx.dpt.dpt_20 import HVACControllerMode, HVACOperationMode, HVACStatus
from xknx.exceptions import DeviceIllegalValue
from xknx.remote_value import GroupAddressesType
from xknx.remote_value.remote_value_climate_mode import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueClimateModeBase,
    RemoteValueControllerMode,
    RemoteValueHVACStatus,
    RemoteValueOperationMode,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class ClimateMode(Device):
    """Class for managing the climate mode."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_operation_mode: GroupAddressesType = None,
        group_address_operation_mode_state: GroupAddressesType = None,
        group_address_operation_mode_protection: GroupAddressesType = None,
        group_address_operation_mode_economy: GroupAddressesType = None,
        group_address_operation_mode_comfort: GroupAddressesType = None,
        group_address_operation_mode_standby: GroupAddressesType = None,
        group_address_controller_status: GroupAddressesType = None,
        group_address_controller_status_state: GroupAddressesType = None,
        group_address_controller_mode: GroupAddressesType = None,
        group_address_controller_mode_state: GroupAddressesType = None,
        group_address_heat_cool: GroupAddressesType = None,
        group_address_heat_cool_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        operation_modes: list[str | HVACOperationMode] | None = None,
        controller_modes: list[str | HVACControllerMode] | None = None,
        device_updated_cb: DeviceCallbackType[ClimateMode] | None = None,
    ) -> None:
        """Initialize ClimateMode class."""
        super().__init__(xknx, name, device_updated_cb)

        self.remote_value_operation_mode = RemoteValueOperationMode(
            xknx,
            group_address=group_address_operation_mode,
            group_address_state=group_address_operation_mode_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode",
            after_update_cb=self._set_internal_operation_mode,
        )
        self.remote_value_controller_mode = RemoteValueControllerMode(
            xknx,
            group_address=group_address_controller_mode,
            group_address_state=group_address_controller_mode_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Controller mode",
            after_update_cb=self._set_internal_controller_mode,
        )
        self.remote_value_controller_status = RemoteValueHVACStatus(
            xknx,
            group_address=group_address_controller_status,
            group_address_state=group_address_controller_status_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Controller status",
            after_update_cb=self._set_internal_modes_from_status,
        )

        self.remote_value_operation_mode_comfort = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_comfort,
            group_address_state=group_address_operation_mode_comfort,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Comfort",
            operation_mode=HVACOperationMode.COMFORT,
            after_update_cb=self._set_internal_operation_mode,
        )
        self.remote_value_operation_mode_standby = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_standby,
            group_address_state=group_address_operation_mode_standby,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Standby",
            operation_mode=HVACOperationMode.STANDBY,
            after_update_cb=self._set_internal_operation_mode,
        )
        self.remote_value_operation_mode_economy = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_economy,
            group_address_state=group_address_operation_mode_economy,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Economy",
            operation_mode=HVACOperationMode.ECONOMY,
            after_update_cb=self._set_internal_operation_mode,
        )
        self.remote_value_operation_mode_protection = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_protection,
            group_address_state=group_address_operation_mode_protection,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Protection",
            operation_mode=HVACOperationMode.BUILDING_PROTECTION,
            after_update_cb=self._set_internal_operation_mode,
        )
        self.remote_value_heat_cool = RemoteValueBinaryHeatCool(
            xknx,
            group_address=group_address_heat_cool,
            group_address_state=group_address_heat_cool_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Heat/Cool",
            controller_mode=HVACControllerMode.HEAT,
            after_update_cb=self._set_internal_controller_mode,
        )

        self.operation_mode = HVACOperationMode.STANDBY
        self.controller_mode = HVACControllerMode.HEAT

        self._operation_modes = self.gather_operation_modes(only_writable=True)
        if operation_modes is not None:
            custom_operation_modes = []
            for op_mode in operation_modes:
                if isinstance(op_mode, str):
                    custom_operation_modes.append(
                        HVACOperationMode[op_mode.replace(" ", "_").upper()]
                    )
                elif isinstance(op_mode, HVACOperationMode):
                    custom_operation_modes.append(op_mode)
            self._operation_modes = [
                mode for mode in custom_operation_modes if mode in self._operation_modes
            ]

        self._controller_modes = self.gather_controller_modes(only_writable=True)
        if controller_modes is not None:
            custom_controller_modes = []
            for ct_mode in controller_modes:
                if isinstance(ct_mode, str):
                    custom_controller_modes.append(
                        HVACControllerMode[ct_mode.replace(" ", "_").upper()]
                    )
                elif isinstance(ct_mode, HVACControllerMode):
                    custom_controller_modes.append(ct_mode)
            self._controller_modes = [
                mode
                for mode in custom_controller_modes
                if mode in self._controller_modes
            ]

        self.supports_operation_mode = bool(
            self.gather_operation_modes(only_writable=False)
        )
        self.supports_controller_mode = bool(
            self.gather_controller_modes(only_writable=False)
        )

    def _iter_remote_values(
        self,
    ) -> Iterator[RemoteValueClimateModeBase[Any]]:
        """Iterate climate mode RemoteValue classes."""
        yield self.remote_value_operation_mode
        yield self.remote_value_controller_mode
        yield self.remote_value_controller_status
        yield self.remote_value_heat_cool
        yield self.remote_value_operation_mode_comfort
        yield self.remote_value_operation_mode_economy
        yield self.remote_value_operation_mode_protection
        yield self.remote_value_operation_mode_standby

    def _set_internal_operation_mode(
        self, operation_mode: HVACOperationMode | None
    ) -> None:
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode is not None and operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            self.after_update()

    def _set_internal_controller_mode(
        self, controller_mode: HVACControllerMode
    ) -> None:
        """Set internal value of controller mode. Call hooks if controller mode was changed."""
        if controller_mode != self.controller_mode:
            self.controller_mode = controller_mode
            self.after_update()

    def _set_internal_modes_from_status(self, status: HVACStatus) -> None:
        """Set internal values from HVACStatus."""
        updated = False
        if status.mode != self.operation_mode:
            self.operation_mode = status.mode
            updated = True
        contr_mode_heat_cool = (
            HVACControllerMode.HEAT
            if status.heat_cool is HeatCool.HEAT
            else HVACControllerMode.COOL
        )
        if contr_mode_heat_cool != self.controller_mode:
            self.controller_mode = contr_mode_heat_cool
            updated = True
        if updated:
            self.after_update()

    async def set_operation_mode(self, operation_mode: HVACOperationMode) -> None:
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if (
            not self.supports_operation_mode
            or operation_mode not in self._operation_modes
        ):
            raise DeviceIllegalValue(
                "operation (preset) mode not supported", operation_mode
            )

        for rv in self._iter_remote_values():
            if rv.writable:
                rv.set_operation_mode(operation_mode)

        self._set_internal_operation_mode(operation_mode)

    async def set_controller_mode(self, controller_mode: HVACControllerMode) -> None:
        """Set the controller mode of a thermostat. Send new controller mode to the bus and update internal state."""
        if (
            not self.supports_controller_mode
            or controller_mode not in self._controller_modes
        ):
            raise DeviceIllegalValue(
                "controller (HVAC) mode not supported", controller_mode
            )

        for rv in self._iter_remote_values():
            if rv.writable:
                rv.set_controller_mode(controller_mode)

        self._set_internal_controller_mode(controller_mode)

    @property
    def operation_modes(self) -> list[HVACOperationMode]:
        """Return all configured operation modes."""
        return self._operation_modes

    @property
    def controller_modes(self) -> list[HVACControllerMode]:
        """Return all configured controller modes."""
        return self._controller_modes

    def gather_operation_modes(
        self, only_writable: bool = True
    ) -> list[HVACOperationMode]:
        """Gather operation modes from RemoteValues."""
        operation_modes: list[HVACOperationMode] = []
        for rv in self._iter_remote_values():
            if rv.initialized:
                if only_writable and not rv.writable:
                    continue
                operation_modes.extend(rv.supported_operation_modes())
        # remove duplicates
        return list(set(operation_modes))

    def gather_controller_modes(
        self, only_writable: bool = True
    ) -> list[HVACControllerMode]:
        """Gather controller modes from RemoteValues."""
        controller_modes: list[HVACControllerMode] = []
        for rv in self._iter_remote_values():
            if rv.initialized:
                if only_writable and not rv.writable:
                    continue
                controller_modes.extend(rv.supported_controller_modes())
        # remove duplicates
        return list(set(controller_modes))

    def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        for rv in self._iter_remote_values():
            rv.process(telegram)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<ClimateMode name="{self.name}" '
            f"operation_mode={self.remote_value_operation_mode.group_addr_str()} "
            f"controller_mode={self.remote_value_controller_mode.group_addr_str()} "
            f"controller_status={self.remote_value_controller_status.group_addr_str()} "
            "/>"
        )
