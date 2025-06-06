"""
Module for managing an DPT Switch remote value.

DPT 1.001.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import GroupAddressesType, RemoteValue, RVCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueSwitch(RemoteValue[bool]):
    """Abstraction for remote value of KNX DPT 1.001 / DPT_Switch."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "State",
        after_update_cb: RVCallbackType[bool] | None = None,
        invert: bool = False,
    ) -> None:
        """Initialize remote value of KNX DPT 1.001."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )
        self.invert = bool(invert)

    def to_knx(self, value: bool) -> DPTBinary:
        """Convert value to payload."""
        if isinstance(value, bool):
            return DPTBinary(value ^ self.invert)
        raise ConversionError(
            "value invalid",
            value=value,
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def from_knx(self, payload: DPTArray | DPTBinary) -> bool:
        """Convert current payload to value."""
        if payload.value == 0:
            return self.invert
        if payload.value == 1:
            return not self.invert
        raise CouldNotParseTelegram(
            "Payload invalid",
            payload=str(payload),
            device_name=self.device_name,
            feature_name=self.feature_name,
        )

    def off(self) -> None:
        """Set value to OFF."""
        self.set(False)

    def on(self) -> None:
        """Set value to ON."""
        # pylint: disable=invalid-name
        self.set(True)
