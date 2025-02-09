"""
Module for managing an RGBW remote value.

DPT 251.600.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary, DPTColorRGBW, RGBWColor

from .remote_value import GroupAddressesType, RemoteValue, RVCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueColorRGBW(RemoteValue[RGBWColor]):
    """Abstraction for remote value of KNX DPT 251.600 (DPT_Color_RGBW)."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Color RGBW",
        after_update_cb: RVCallbackType[RGBWColor] | None = None,
    ) -> None:
        """Initialize remote value of KNX DPT 251.600 (DPT_Color_RGBW)."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )
        self._valid_value = RGBWColor()

    def to_knx(self, value: RGBWColor) -> DPTArray | DPTBinary:
        """Convert value to payload."""
        return DPTColorRGBW.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> RGBWColor:
        """
        Convert current payload to value.

        If one element is invalid, use the last received value.
        """
        new_value = DPTColorRGBW.from_knx(payload)
        self._valid_value = self._valid_value | new_value
        return self._valid_value
