"""
Module for managing an RGB remote value.

DPT 232.600.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_color import DPTColorRGB, RGBColor

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueColorRGB(RemoteValue[RGBColor]):
    """Abstraction for remote value of KNX DPT 232.600 (DPT_Color_RGB)."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Color RGB",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize remote value of KNX DPT 232.600 (DPT_Color_RGB)."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def to_knx(self, value: RGBColor) -> DPTArray:
        """Convert value to payload."""
        return DPTColorRGB.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> RGBColor:
        """Convert current payload to value."""
        return DPTColorRGB.from_knx(payload)
