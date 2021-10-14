"""
Module for managing an DPT Step remote value.

DPT 1.007.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueStep(RemoteValue[DPTBinary, "RemoteValueStep.Direction"]):
    """Abstraction for remote value of KNX DPT 1.007 / DPT_Step."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        DECREASE = 0
        INCREASE = 1

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        device_name: str | None = None,
        feature_name: str = "Step",
        after_update_cb: AsyncCallbackType | None = None,
        invert: bool = False,
    ):
        """Initialize remote value of KNX DPT 1.007."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )
        self.invert = invert

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTBinary | None:
        """Test if telegram payload may be parsed."""
        return payload if isinstance(payload, DPTBinary) else None

    # from KNX Association System Specifications AS v1.5.00:
    # 1.007 DPT_Step   0 = Decrease 1 = Increase
    # 1.008 DPT_UpDown 0 = Up       1 = Down

    def to_knx(self, value: RemoteValueStep.Direction) -> DPTBinary:
        """Convert value to payload."""
        if value == self.Direction.INCREASE:
            return DPTBinary(0) if self.invert else DPTBinary(1)
        if value == self.Direction.DECREASE:
            return DPTBinary(1) if self.invert else DPTBinary(0)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: DPTBinary) -> RemoteValueStep.Direction:
        """Convert current payload to value."""
        if payload == DPTBinary(1):
            return self.Direction.DECREASE if self.invert else self.Direction.INCREASE
        if payload == DPTBinary(0):
            return self.Direction.INCREASE if self.invert else self.Direction.DECREASE
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=payload,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    async def increase(self) -> None:
        """Increase value."""
        await self.set(self.Direction.INCREASE)

    async def decrease(self) -> None:
        """Decrease the value."""
        await self.set(self.Direction.DECREASE)
