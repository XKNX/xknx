"""
Module for managing setpoint shifting.

DPT 6.010.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary, DPTTemperature, DPTValue1Count
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import GroupAddressesType, RemoteValue, RVCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class SetpointShiftMode(Enum):
    """Enum for setting the setpoint shift mode."""

    DPT6010 = DPTValue1Count
    DPT9002 = DPTTemperature


class RemoteValueSetpointShift(RemoteValue[float]):
    """Abstraction for remote value of KNX DPT 6.010."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        after_update_cb: RVCallbackType[float] | None = None,
        setpoint_shift_mode: SetpointShiftMode | None = None,
        setpoint_shift_step: float = 0.1,
    ) -> None:
        """Initialize RemoteValueSetpointShift class."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name="Setpoint shift value",
            after_update_cb=after_update_cb,
        )

        self._internal_dpt_class: type[DPTValue1Count | DPTTemperature] | None = (
            setpoint_shift_mode.value if setpoint_shift_mode is not None else None
        )
        self.setpoint_shift_step = setpoint_shift_step

    def to_knx(self, value: float) -> DPTArray:
        """Convert value to payload."""
        if self._internal_dpt_class is None:
            raise ConversionError(
                f"Setpoint shift DPT not initialized for {self.device_name}"
            )
        if self._internal_dpt_class == DPTValue1Count:
            converted_value = int(value / self.setpoint_shift_step)
            return DPTValue1Count.to_knx(converted_value)
        return DPTTemperature.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> float:
        """Convert current payload to value."""
        if self._internal_dpt_class is None:
            self._internal_dpt_class = self._determine_dpt_class(payload)

        payload_value = self._internal_dpt_class.from_knx(payload)
        if self._internal_dpt_class == DPTValue1Count:
            return payload_value * self.setpoint_shift_step
        return payload_value

    def _determine_dpt_class(
        self, payload: DPTArray | DPTBinary
    ) -> type[DPTValue1Count | DPTTemperature]:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray):
            payload_length = len(payload.value)
            if payload_length == DPTTemperature.payload_length:
                return DPTTemperature
            if payload_length == DPTValue1Count.payload_length:
                return DPTValue1Count
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))
