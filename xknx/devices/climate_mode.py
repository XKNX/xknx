"""
Module for managing operation and controller modes.

Operation modes can be 'auto', 'comfort', 'standby', 'economy', 'protection' and use either a binary DPT or DPT 20.102.
Controller modes use DPT 20.105.
"""
from __future__ import annotations

from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING, Any

from xknx.dpt.dpt_hvac_mode import HVACControllerMode, HVACOperationMode
from xknx.exceptions import DeviceIllegalValue
from xknx.remote_value import GroupAddressesType, RemoteValue
from xknx.remote_value.remote_value_climate_mode import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueClimateModeBase,
    RemoteValueControllerMode,
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
        group_address_operation_mode: GroupAddressesType | None = None,
        group_address_operation_mode_state: GroupAddressesType | None = None,
        group_address_operation_mode_protection: GroupAddressesType | None = None,
        group_address_operation_mode_night: GroupAddressesType | None = None,
        group_address_operation_mode_comfort: GroupAddressesType | None = None,
        group_address_operation_mode_standby: GroupAddressesType | None = None,
        group_address_controller_status: GroupAddressesType | None = None,
        group_address_controller_status_state: GroupAddressesType | None = None,
        group_address_controller_mode: GroupAddressesType | None = None,
        group_address_controller_mode_state: GroupAddressesType | None = None,
        group_address_heat_cool: GroupAddressesType | None = None,
        group_address_heat_cool_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        operation_modes: list[str | HVACOperationMode] | None = None,
        controller_modes: list[str | HVACControllerMode] | None = None,
        device_updated_cb: DeviceCallbackType[ClimateMode] | None = None,
    ):
        """Initialize ClimateMode class."""
        super().__init__(xknx, name, device_updated_cb)

        self.remote_value_operation_mode = RemoteValueOperationMode(
            xknx,
            group_address=group_address_operation_mode,
            group_address_state=group_address_operation_mode_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode",
            climate_mode_type=RemoteValueOperationMode.ClimateModeType.HVAC_MODE,
            after_update_cb=None,
        )
        self.remote_value_controller_mode = RemoteValueControllerMode(
            xknx,
            group_address=group_address_controller_mode,
            group_address_state=group_address_controller_mode_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Controller mode",
            after_update_cb=None,
        )
        self.remote_value_controller_status = RemoteValueOperationMode(
            xknx,
            group_address=group_address_controller_status,
            group_address_state=group_address_controller_status_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Controller status",
            climate_mode_type=RemoteValueOperationMode.ClimateModeType.CONTROLLER_STATUS,
            after_update_cb=None,
        )

        self.remote_value_operation_mode_comfort = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_comfort,
            group_address_state=group_address_operation_mode_comfort,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Comfort",
            operation_mode=HVACOperationMode.COMFORT,
            after_update_cb=None,
        )
        self.remote_value_operation_mode_standby = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_standby,
            group_address_state=group_address_operation_mode_standby,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Standby",
            operation_mode=HVACOperationMode.STANDBY,
            after_update_cb=None,
        )
        self.remote_value_operation_mode_night = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_night,
            group_address_state=group_address_operation_mode_night,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Night",
            operation_mode=HVACOperationMode.NIGHT,
            after_update_cb=None,
        )
        self.remote_value_operation_mode_protection = RemoteValueBinaryOperationMode(
            xknx,
            group_address=group_address_operation_mode_protection,
            group_address_state=group_address_operation_mode_protection,
            sync_state=sync_state,
            device_name=name,
            feature_name="Operation mode Protection",
            operation_mode=HVACOperationMode.FROST_PROTECTION,
            after_update_cb=None,
        )
        self.remote_value_heat_cool = RemoteValueBinaryHeatCool(
            xknx,
            group_address=group_address_heat_cool,
            group_address_state=group_address_heat_cool_state,
            sync_state=sync_state,
            device_name=name,
            feature_name="Heat/Cool",
            controller_mode=HVACControllerMode.HEAT,
            after_update_cb=None,
        )

        self.operation_mode = HVACOperationMode.STANDBY
        self.controller_mode = HVACControllerMode.HEAT

        self._operation_modes: list[HVACOperationMode] = []
        if operation_modes is None:
            self._operation_modes = self.gather_operation_modes()
        else:
            for op_mode in operation_modes:
                if isinstance(op_mode, str):
                    self._operation_modes.append(HVACOperationMode(op_mode))
                elif isinstance(op_mode, HVACOperationMode):
                    self._operation_modes.append(op_mode)

        self._controller_modes: list[HVACControllerMode] = []
        if controller_modes is None:
            self._controller_modes = self.gather_controller_modes()
        else:
            for ct_mode in controller_modes:
                if isinstance(ct_mode, str):
                    self._controller_modes.append(HVACControllerMode(ct_mode))
                elif isinstance(ct_mode, HVACControllerMode):
                    self._controller_modes.append(ct_mode)

        self.supports_operation_mode = any(
            operation_mode.initialized
            for operation_mode in self._iter_operation_remote_values()
        )
        self.supports_controller_mode = any(
            controller_mode.initialized
            for controller_mode in self._iter_controller_remote_values()
        )
        self._use_binary_operation_modes = any(
            operation_mode.initialized
            for operation_mode in self._iter_binary_operation_modes()
        )

    def _iter_remote_values(
        self,
    ) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate climate mode RemoteValue classes."""
        return chain(
            self._iter_operation_remote_values(),
            self._iter_controller_remote_values(),
        )

    def _iter_operation_remote_values(
        self,
    ) -> Iterator[RemoteValueClimateModeBase[Any, HVACOperationMode]]:
        return chain(
            self._iter_binary_operation_modes(),
            self._iter_byte_operation_modes(),
        )

    def _iter_binary_operation_modes(
        self,
    ) -> Iterator[RemoteValueClimateModeBase[Any, HVACOperationMode]]:
        """Iterate DPT 1 binary operation modes."""
        yield from (
            self.remote_value_operation_mode_comfort,
            self.remote_value_operation_mode_night,
            self.remote_value_operation_mode_protection,
            self.remote_value_operation_mode_standby,
        )

    def _iter_byte_operation_modes(
        self,
    ) -> Iterator[RemoteValueClimateModeBase[Any, HVACOperationMode]]:
        """Iterate normal DPT 20.102 operation mode remote values."""
        yield from (
            self.remote_value_operation_mode,
            self.remote_value_controller_status,
        )

    def _iter_controller_remote_values(
        self,
    ) -> Iterator[RemoteValueClimateModeBase[Any, HVACControllerMode]]:
        """Iterate DPT 20.105 controller remote values."""
        yield self.remote_value_controller_mode
        yield self.remote_value_heat_cool

    async def _set_internal_operation_mode(
        self, operation_mode: HVACOperationMode
    ) -> None:
        """Set internal value of operation mode. Call hooks if operation mode was changed."""
        if operation_mode != self.operation_mode:
            self.operation_mode = operation_mode
            await self.after_update()

    async def _set_internal_controller_mode(
        self, controller_mode: HVACControllerMode
    ) -> None:
        """Set internal value of controller mode. Call hooks if controller mode was changed."""
        if controller_mode != self.controller_mode:
            self.controller_mode = controller_mode
            await self.after_update()

    async def set_operation_mode(self, operation_mode: HVACOperationMode) -> None:
        """Set the operation mode of a thermostat. Send new operation_mode to BUS and update internal state."""
        if (
            not self.supports_operation_mode
            or operation_mode not in self._operation_modes
        ):
            raise DeviceIllegalValue(
                "operation (preset) mode not supported", str(operation_mode)
            )

        rv_operation: RemoteValueClimateModeBase[Any, HVACOperationMode]
        for rv_operation in self._iter_operation_remote_values():
            if (
                rv_operation.writable
                and operation_mode in rv_operation.supported_operation_modes()
            ):
                await rv_operation.set(operation_mode)

        await self._set_internal_operation_mode(operation_mode)

    async def set_controller_mode(self, controller_mode: HVACControllerMode) -> None:
        """Set the controller mode of a thermostat. Send new controller mode to the bus and update internal state."""
        if (
            not self.supports_controller_mode
            or controller_mode not in self._controller_modes
        ):
            raise DeviceIllegalValue(
                "controller (HVAC) mode not supported", str(controller_mode)
            )

        rv_controller: RemoteValueClimateModeBase[Any, HVACControllerMode]
        for rv_controller in self._iter_controller_remote_values():
            if (
                rv_controller.writable
                and controller_mode in rv_controller.supported_operation_modes()
            ):
                await rv_controller.set(controller_mode)

        await self._set_internal_controller_mode(controller_mode)

    @property
    def operation_modes(self) -> list[HVACOperationMode]:
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []
        return self._operation_modes

    @property
    def controller_modes(self) -> list[HVACControllerMode]:
        """Return all configured controller modes."""
        if not self.supports_controller_mode:
            return []
        return self._controller_modes

    def gather_operation_modes(self) -> list[HVACOperationMode]:
        """Gather operation modes from RemoteValues."""
        operation_modes: list[HVACOperationMode] = []
        for rv_operation in self._iter_operation_remote_values():
            if rv_operation.writable:
                operation_modes.extend(rv_operation.supported_operation_modes())
        # remove duplicates
        return list(set(operation_modes))

    def gather_controller_modes(self) -> list[HVACControllerMode]:
        """Gather controller modes from RemoteValues."""
        controller_modes: list[HVACControllerMode] = []
        for rv_controller in self._iter_controller_remote_values():
            if rv_controller.writable:
                controller_modes.extend(rv_controller.supported_operation_modes())
        # remove duplicates
        return list(set(controller_modes))

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        if self.supports_operation_mode:
            for rv_mode in self._iter_operation_remote_values():
                if await rv_mode.process(telegram):
                    #  ignore inactive RemoteValueBinaryOperationMode
                    if rv_mode.value:
                        await self._set_internal_operation_mode(rv_mode.value)
                        return

        if self.supports_controller_mode:
            for rv_controller in self._iter_controller_remote_values():
                if await rv_controller.process(telegram):
                    if rv_controller.value is not None:
                        await self._set_internal_controller_mode(rv_controller.value)
                    return

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<ClimateMode name="{self.name}" '
            f"operation_mode={self.remote_value_operation_mode.group_addr_str()} "
            f"controller_mode={self.remote_value_controller_mode.group_addr_str()} "
            f"controller_status={self.remote_value_controller_status.group_addr_str()} "
            "/>"
        )
