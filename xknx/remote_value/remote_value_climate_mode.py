"""
Module for managing an climate mode remote values.

DPT .
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from xknx.dpt import (
    DPTArray,
    DPTBinary,
    DPTHVACContrMode,
    DPTHVACMode,
    DPTHVACStatus,
)
from xknx.dpt.dpt_1 import HeatCool
from xknx.dpt.dpt_20 import HVACControllerMode, HVACOperationMode, HVACStatus
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import (
    GroupAddressesType,
    RemoteValue,
    RVCallbackType,
)

if TYPE_CHECKING:
    from xknx.xknx import XKNX


HVACModeT = TypeVar(
    "HVACModeT",
    HVACControllerMode,
    HVACOperationMode,
    HVACStatus,
    HVACOperationMode | None,
)


class RemoteValueClimateModeBase(RemoteValue[HVACModeT]):
    """Base class for binary climate mode remote values."""

    @abstractmethod
    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""

    @abstractmethod
    def set_operation_mode(self, mode: HVACOperationMode) -> None:
        """Set operation mode. Return if not supported."""

    @abstractmethod
    def supported_controller_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported controller modes."""

    @abstractmethod
    def set_controller_mode(self, mode: HVACControllerMode) -> None:
        """Set controller mode. Return if not supported."""


class RemoteValueOperationMode(RemoteValueClimateModeBase[HVACOperationMode]):
    """Abstraction for remote value of KNX climate operation modes."""

    dpt_class = DPTHVACMode

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Climate mode",
        after_update_cb: RVCallbackType[HVACOperationMode] | None = None,
    ) -> None:
        """Initialize remote value of KNX climate mode."""
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""
        return self.dpt_class.get_valid_values()

    def set_operation_mode(self, mode: HVACOperationMode) -> None:
        """Set operation mode. Return if not supported."""
        if mode not in self.supported_operation_modes():
            return
        super().set(mode)

    def supported_controller_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported controller modes."""
        return []

    def set_controller_mode(self, mode: HVACControllerMode) -> None:
        """Set controller mode. Return if not supported."""
        return


class RemoteValueControllerMode(RemoteValueClimateModeBase[HVACControllerMode]):
    """Abstraction for remote value of KNX climate controller modes."""

    dpt_class = DPTHVACContrMode

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Controller Mode",
        after_update_cb: RVCallbackType[HVACControllerMode] | None = None,
    ) -> None:
        """Initialize remote value of KNX climate mode."""
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""
        return []

    def set_operation_mode(self, mode: HVACOperationMode) -> None:
        """Set operation mode. Return if not supported."""
        return

    def supported_controller_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported controller modes."""
        return DPTHVACContrMode.get_valid_values()

    def set_controller_mode(self, mode: HVACControllerMode) -> None:
        """Set controller mode. Return if not supported."""
        if mode not in self.supported_controller_modes():
            return
        super().set(mode)


class RemoteValueHVACStatus(RemoteValueClimateModeBase[HVACStatus]):
    """Abstraction for remote value of KNX climate HVAC status (Eberle status)."""

    dpt_class = DPTHVACStatus

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Controller status",
        after_update_cb: RVCallbackType[HVACStatus] | None = None,
    ) -> None:
        """Initialize remote value of KNX climate controller status."""
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""
        return [
            HVACOperationMode.COMFORT,
            HVACOperationMode.STANDBY,
            HVACOperationMode.ECONOMY,
            HVACOperationMode.BUILDING_PROTECTION,
        ]

    def set_operation_mode(self, mode: HVACOperationMode) -> None:
        """Set operation mode. Return if not supported."""
        if mode not in self.supported_operation_modes():
            return
        if self._value is None:
            raise ConversionError(
                "HVACStatus value not initialized. Can not write new mode.",
                device_name=self.device_name,
            )
        new_status = HVACStatus(
            mode=mode,
            dew_point=self._value.dew_point,
            heat_cool=self._value.heat_cool,
            inactive=self._value.inactive,
            frost_alarm=self._value.frost_alarm,
        )
        return super().set(new_status)

    def supported_controller_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported controller modes."""
        return [HVACControllerMode.HEAT, HVACControllerMode.COOL]

    def set_controller_mode(self, mode: HVACControllerMode) -> None:
        """Set controller mode. Return if not supported."""
        if mode not in self.supported_controller_modes():
            return
        if self._value is None:
            raise ConversionError(
                "HVACStatus value not initialized. Can not write new mode.",
                device_name=self.device_name,
            )
        new_status = HVACStatus(
            mode=self._value.mode,
            dew_point=self._value.dew_point,
            heat_cool=HeatCool.HEAT
            if mode == HVACControllerMode.HEAT
            else HeatCool.COOL,
            inactive=self._value.inactive,
            frost_alarm=self._value.frost_alarm,
        )
        super().set(new_status)


class RemoteValueBinaryOperationMode(
    RemoteValueClimateModeBase[HVACOperationMode | None]
):
    """Abstraction for remote value of split up KNX climate modes."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Climate mode binary",
        after_update_cb: RVCallbackType[HVACOperationMode | None] | None = None,
        operation_mode: HVACOperationMode | None = None,
    ) -> None:
        """Initialize remote value of KNX DPT 1 representing a climate operation mode."""
        if not isinstance(operation_mode, HVACOperationMode):
            raise ConversionError(
                "Invalid operation mode type",
                operation_mode=str(operation_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        self.operation_mode = operation_mode
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""
        # all binary operation modes off -> Standby according to MDT
        return (
            [self.operation_mode, HVACOperationMode.STANDBY]
            if self.operation_mode is not HVACOperationMode.STANDBY
            else [HVACOperationMode.STANDBY]
        )

    def set_operation_mode(self, mode: HVACOperationMode) -> None:
        """Set operation mode. Return if not supported."""
        super().set(mode)

    def supported_controller_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported controller modes."""
        return []

    def set_controller_mode(self, mode: HVACControllerMode) -> None:
        """Set controller mode. Return if not supported."""
        return

    def to_knx(self, value: HVACOperationMode | None) -> DPTBinary:
        """Convert value to payload."""
        if isinstance(value, HVACOperationMode):
            # foreign operation modes will set the RemoteValue to False
            return DPTBinary(value == self.operation_mode)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: DPTArray | DPTBinary) -> HVACOperationMode | None:
        """Convert current payload to value."""
        if payload.value == 1:
            return self.operation_mode
        if payload.value == 0:
            return None
        raise CouldNotParseTelegram(
            "Payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )


class RemoteValueBinaryHeatCool(RemoteValueClimateModeBase[HVACControllerMode]):
    """Abstraction for remote value of heat/cool controller mode."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Controller mode Heat/Cool",
        after_update_cb: RVCallbackType[HVACControllerMode] | None = None,
        controller_mode: HVACControllerMode | None = None,
    ) -> None:
        """Initialize remote value of KNX DPT 1 representing a climate controller mode."""
        if not isinstance(controller_mode, HVACControllerMode):
            raise ConversionError(
                "Invalid controller mode type",
                controller_mode=str(controller_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        if controller_mode not in self.supported_controller_modes():
            raise ConversionError(
                "Controller mode not supported for binary mode object",
                controller_mode=str(controller_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        self.controller_mode = controller_mode
        super().__init__(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""
        return []

    def set_operation_mode(self, mode: HVACOperationMode) -> None:
        """Set operation mode. Return if not supported."""
        return

    def supported_controller_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported controller modes."""
        return [HVACControllerMode.HEAT, HVACControllerMode.COOL]

    def set_controller_mode(self, mode: HVACControllerMode) -> None:
        """Set controller mode. Return if not supported."""
        if mode not in self.supported_controller_modes():
            return
        super().set(mode)

    def to_knx(self, value: Any) -> DPTBinary:
        """Convert value to payload."""
        if isinstance(value, HVACControllerMode):
            # foreign operation modes will set the RemoteValue to False
            return DPTBinary(value == self.controller_mode)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: DPTArray | DPTBinary) -> HVACControllerMode:
        """Convert current payload to value."""
        if payload.value == 1:
            return self.controller_mode
        if payload.value == 0:
            # return the other operation mode
            return next(
                _op
                for _op in self.supported_controller_modes()
                if _op is not self.controller_mode
            )
        raise CouldNotParseTelegram(
            "Payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )
