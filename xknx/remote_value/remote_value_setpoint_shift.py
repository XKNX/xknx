"""
Module for managing setpoint shifting.

DPT 6.010.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary, DPTValue1Count

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueSetpointShift(RemoteValue[DPTArray, float]):
    """Abstraction for remote value of KNX DPT 6.010."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        device_name: str | None = None,
        after_update_cb: AsyncCallbackType | None = None,
        setpoint_shift_step: float = 0.1,
    ):
        """Initialize RemoteValueSetpointShift class."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            device_name=device_name,
            feature_name="Setpoint shift value",
            after_update_cb=after_update_cb,
        )

        self.setpoint_shift_step = setpoint_shift_step

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray | None:
        """Test if telegram payload may be parsed."""
        # pylint: disable=no-self-use
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 1
            else None
        )

    def to_knx(self, value: float) -> DPTArray:
        """Convert value to payload."""
        converted_value = int(value / self.setpoint_shift_step)
        return DPTArray(DPTValue1Count.to_knx(converted_value))

    def from_knx(self, payload: DPTArray) -> float:
        """Convert current payload to value."""
        converted_payload = DPTValue1Count.from_knx(payload.value)
        return converted_payload * self.setpoint_shift_step
