"""
Module for managing operation and controller modes.

Operation modes can be 'auto', 'comfort', 'standby', 'economy', 'protection' and use either a binary DPT or DPT 20.102.
Controller modes use DPT 20.105.
"""
from itertools import chain
from typing import TYPE_CHECKING, Any, Iterator, List, Optional, Union

from xknx.dpt.dpt_hvac_mode import HVACControllerMode, HVACOperationMode
from xknx.exceptions import DeviceIllegalValue
from xknx.remote_value.remote_value_climate_mode import (
    RemoteValueBinaryHeatCool,
    RemoteValueBinaryOperationMode,
    RemoteValueClimateMode,
    RemoteValueClimateModeBase,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.remote_value import RemoteValue
    from xknx.telegram import Telegram
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX


class ClimateMode(Device):
    """Class for managing the climate mode."""

    # pylint: disable=invalid-name,too-many-instance-attributes

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address_operation_mode: Optional["GroupAddressableType"] = None,
        group_address_operation_mode_state: Optional["GroupAddressableType"] = None,
        group_address_operation_mode_protection: Optional[
            "GroupAddressableType"
        ] = None,
        group_address_operation_mode_night: Optional["GroupAddressableType"] = None,
        group_address_operation_mode_comfort: Optional["GroupAddressableType"] = None,
        group_address_operation_mode_standby: Optional["GroupAddressableType"] = None,
        group_address_controller_status: Optional["GroupAddressableType"] = None,
        group_address_controller_status_state: Optional["GroupAddressableType"] = None,
        group_address_controller_mode: Optional["GroupAddressableType"] = None,
        group_address_controller_mode_state: Optional["GroupAddressableType"] = None,
        group_address_heat_cool: Optional["GroupAddressableType"] = None,
        group_address_heat_cool_state: Optional["GroupAddressableType"] = None,
        operation_modes: Optional[List[Union[str, HVACOperationMode]]] = None,
        controller_modes: Optional[List[Union[str, HVACControllerMode]]] = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize ClimateMode class."""
        # pylint: disable=too-many-arguments, too-many-locals, too-many-branches, too-many-statements
        super().__init__(xknx, name, device_updated_cb)

        self.remote_value_operation_mode: RemoteValueClimateMode[
            HVACOperationMode
        ] = RemoteValueClimateMode(
            xknx,
            group_address=group_address_operation_mode,
            group_address_state=group_address_operation_mode_state,
            sync_state=True,
            device_name=name,
            feature_name="Operation mode",
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_MODE,
            after_update_cb=None,
        )
        self.remote_value_controller_mode: RemoteValueClimateMode[
            HVACControllerMode
        ] = RemoteValueClimateMode(
            xknx,
            group_address=group_address_controller_mode,
            group_address_state=group_address_controller_mode_state,
            sync_state=True,
            device_name=name,
            feature_name="Controller mode",
            climate_mode_type=RemoteValueClimateMode.ClimateModeType.HVAC_CONTR_MODE,
            after_update_cb=None,
        )
        self.remote_value_controller_status: RemoteValueClimateMode[
            HVACOperationMode
        ] = RemoteValueClimateMode(
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

        self._operation_modes: List[HVACOperationMode] = []
        if operation_modes is None:
            self._operation_modes = self.gather_operation_modes()
        else:
            for op_mode in operation_modes:
                if isinstance(op_mode, str):
                    self._operation_modes.append(HVACOperationMode(op_mode))
                elif isinstance(op_mode, HVACOperationMode):
                    self._operation_modes.append(op_mode)

        self._controller_modes: List[HVACControllerMode] = []
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
    def from_config(cls, xknx: "XKNX", name: str, config: Any) -> "ClimateMode":
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

    def _iter_remote_values(
        self,
    ) -> Iterator["RemoteValue"]:
        """Iterate climate mode RemoteValue classes."""
        return chain(
            self._iter_byte_operation_modes(),
            self._iter_controller_remote_values(),
            self._iter_binary_operation_modes(),
        )

    def _iter_byte_operation_modes(
        self,
    ) -> Iterator[RemoteValueClimateMode[HVACOperationMode]]:
        """Iterate normal DPT 20.102 operation mode remote values."""
        yield from (
            self.remote_value_operation_mode,
            self.remote_value_controller_status,
        )

    def _iter_controller_remote_values(
        self,
    ) -> Iterator[RemoteValueClimateModeBase[HVACControllerMode]]:
        """Iterate DPT 20.105 controller remote values."""
        yield from (
            self.remote_value_controller_mode,
            self.remote_value_heat_cool,
        )

    def _iter_binary_operation_modes(self) -> Iterator[RemoteValueBinaryOperationMode]:
        """Iterate DPT 1 binary operation modes."""
        yield from (
            self.remote_value_operation_mode_comfort,
            self.remote_value_operation_mode_night,
            self.remote_value_operation_mode_protection,
            self.remote_value_operation_mode_standby,
        )

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

        rv: RemoteValueClimateModeBase[HVACOperationMode]
        for rv in chain(
            self._iter_byte_operation_modes(), self._iter_binary_operation_modes()
        ):
            if rv.writable and operation_mode in rv.supported_operation_modes():
                await rv.set(operation_mode)

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

        rv: RemoteValueClimateModeBase[HVACControllerMode]
        for rv in self._iter_controller_remote_values():
            if rv.writable and controller_mode in rv.supported_operation_modes():
                await rv.set(controller_mode)

        await self._set_internal_controller_mode(controller_mode)

    @property
    def operation_modes(self) -> List[HVACOperationMode]:
        """Return all configured operation modes."""
        if not self.supports_operation_mode:
            return []
        return self._operation_modes

    @property
    def controller_modes(self) -> List[HVACControllerMode]:
        """Return all configured controller modes."""
        if not self.supports_controller_mode:
            return []
        return self._controller_modes

    def gather_operation_modes(self) -> List[HVACOperationMode]:
        """Gather operation modes from RemoteValues."""
        operation_modes: List[HVACOperationMode] = []
        for rv in chain(
            self._iter_binary_operation_modes(), self._iter_byte_operation_modes()
        ):
            if rv.writable:
                operation_modes.extend(rv.supported_operation_modes())
        # remove duplicates
        return list(set(operation_modes))

    def gather_controller_modes(self) -> List[HVACControllerMode]:
        """Gather controller modes from RemoteValues."""
        controller_modes: List[HVACControllerMode] = []
        for rv in self._iter_controller_remote_values():
            if rv.writable:
                controller_modes.extend(rv.supported_operation_modes())
        # remove duplicates
        return list(set(controller_modes))

    async def process_group_write(self, telegram: "Telegram") -> None:
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

    def __str__(self) -> str:
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
