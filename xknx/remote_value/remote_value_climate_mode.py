"""
Module for managing an climate mode remote values.

DPT .
"""
from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from xknx.dpt import (
    DPTArray,
    DPTBinary,
    DPTControllerStatus,
    DPTHVACContrMode,
    DPTHVACMode,
)
from xknx.dpt.dpt_hvac_mode import HVACControllerMode, HVACModeT, HVACOperationMode
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import (
    AsyncCallbackType,
    DPTPayloadT,
    GroupAddressesType,
    RemoteValue,
)

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueClimateModeBase(RemoteValue[DPTPayloadT, Optional[HVACModeT]]):
    """Base class for binary climate mode remote values."""

    @abstractmethod
    def supported_operation_modes(
        self,
    ) -> list[HVACModeT]:
        """Return a list of all supported operation modes."""


class RemoteValueOperationMode(RemoteValueClimateModeBase[DPTArray, HVACOperationMode]):
    """Abstraction for remote value of KNX climate operation modes."""

    class ClimateModeType(Enum):
        """Implemented climate mode types."""

        CONTROLLER_STATUS = DPTControllerStatus
        HVAC_MODE = DPTHVACMode

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Climate mode",
        climate_mode_type: ClimateModeType | None = None,
        after_update_cb: AsyncCallbackType | None = None,
    ):
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
        if not isinstance(climate_mode_type, self.ClimateModeType):
            raise ConversionError(
                "invalid climate mode type",
                climate_mode_type=str(climate_mode_type),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        self._climate_mode_transcoder: (
            DPTControllerStatus | DPTHVACMode
        ) = climate_mode_type.value

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of all supported operation modes."""
        return list(self._climate_mode_transcoder.SUPPORTED_MODES.values())

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == 1:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: Any) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(self._climate_mode_transcoder.to_knx(value))

    def from_knx(self, payload: DPTArray) -> HVACOperationMode | None:
        """Convert current payload to value."""
        return self._climate_mode_transcoder.from_knx(payload.value)


class RemoteValueControllerMode(
    RemoteValueClimateModeBase[DPTArray, HVACControllerMode]
):
    """Abstraction for remote value of KNX climate controller modes."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Controller Mode",
        after_update_cb: AsyncCallbackType | None = None,
    ):
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

    def supported_operation_modes(self) -> list[HVACControllerMode]:
        """Return a list of all supported operation modes."""
        return list(DPTHVACContrMode.SUPPORTED_MODES.values())

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == 1:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: Any) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTHVACContrMode.to_knx(value))

    def from_knx(self, payload: DPTArray) -> HVACControllerMode | None:
        """Convert current payload to value."""
        return DPTHVACContrMode.from_knx(payload.value)


class RemoteValueBinaryOperationMode(
    RemoteValueClimateModeBase[DPTBinary, HVACOperationMode]
):
    """Abstraction for remote value of split up KNX climate modes."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Climate mode binary",
        after_update_cb: AsyncCallbackType | None = None,
        operation_mode: HVACOperationMode | None = None,
    ):
        """Initialize remote value of KNX DPT 1 representing a climate operation mode."""
        if not isinstance(operation_mode, HVACOperationMode):
            raise ConversionError(
                "Invalid operation mode type",
                operation_mode=str(operation_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        if operation_mode not in self.supported_operation_modes():
            raise ConversionError(
                "Operation mode not supported for binary mode object",
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

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTBinary:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTBinary):
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: Any) -> DPTBinary:
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

    def supported_operation_modes(self) -> list[HVACOperationMode]:
        """Return a list of the configured operation mode."""
        return [
            HVACOperationMode.COMFORT,
            HVACOperationMode.FROST_PROTECTION,
            HVACOperationMode.NIGHT,
            HVACOperationMode.STANDBY,
        ]

    def from_knx(self, payload: DPTPayloadT) -> HVACOperationMode | None:
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.operation_mode
        if payload == DPTBinary(0):
            return None
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )


class RemoteValueBinaryHeatCool(
    RemoteValueClimateModeBase[DPTBinary, HVACControllerMode]
):
    """Abstraction for remote value of heat/cool controller mode."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Controller mode Heat/Cool",
        after_update_cb: AsyncCallbackType | None = None,
        controller_mode: HVACControllerMode | None = None,
    ):
        """Initialize remote value of KNX DPT 1 representing a climate controller mode."""
        if not isinstance(controller_mode, HVACControllerMode):
            raise ConversionError(
                "Invalid controller mode type",
                controller_mode=str(controller_mode),
                device_name=str(device_name),
                feature_name=feature_name,
            )
        if controller_mode not in self.supported_operation_modes():
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

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTBinary:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTBinary):
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def supported_operation_modes(self) -> list[HVACControllerMode]:
        """Return a list of the configured operation mode."""
        return [HVACControllerMode.HEAT, HVACControllerMode.COOL]

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

    def from_knx(self, payload: DPTPayloadT) -> HVACControllerMode | None:
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.controller_mode
        if payload == DPTBinary(0):
            # return the other operation mode
            return next(
                (
                    _op
                    for _op in self.supported_operation_modes()
                    if _op is not self.controller_mode
                ),
                None,
            )
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )
