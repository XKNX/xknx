"""
Module for managing an DPT Up/Down remote value.

DPT 1.008.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueUpDown(RemoteValue[DPTBinary, "RemoteValueUpDown.Direction"]):
    """Abstraction for remote value of KNX DPT 1.008 / DPT_UpDown."""

    class Direction(Enum):
        """Enum for indicating the direction."""

        UP = 0
        DOWN = 1

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        device_name: str | None = None,
        feature_name: str = "Up/Down",
        after_update_cb: AsyncCallbackType | None = None,
        invert: bool = False,
    ):
        """Initialize remote value of KNX DPT 1.008."""
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

    def to_knx(self, value: RemoteValueUpDown.Direction) -> DPTBinary:
        """Convert value to payload."""
        if value == self.Direction.UP:
            return DPTBinary(1) if self.invert else DPTBinary(0)
        if value == self.Direction.DOWN:
            return DPTBinary(0) if self.invert else DPTBinary(1)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: DPTBinary) -> RemoteValueUpDown.Direction:
        """Convert current payload to value."""
        if payload == DPTBinary(0):
            return self.Direction.DOWN if self.invert else self.Direction.UP
        if payload == DPTBinary(1):
            return self.Direction.UP if self.invert else self.Direction.DOWN
        raise CouldNotParseTelegram(
            "payload invalid",
            payload=payload,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    async def down(self) -> None:
        """Set value to down."""
        await self.set(self.Direction.DOWN)

    async def up(self) -> None:
        """Set value to UP."""
        # pylint: disable=invalid-name
        await self.set(self.Direction.UP)
