"""
Module for managing an xyY-color remote value.

DPT 242.600.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary
from xknx.dpt.dpt_color import DPTColorXYY, XYYColor
from xknx.exceptions import CouldNotParseTelegram

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueColorXYY(RemoteValue[DPTArray, XYYColor]):
    """Abstraction for remote value of KNX DPT 242.600 (DPT_Colour_xyY)."""

    PAYLOAD_LENGTH = 6

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Color xyY",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize remote value of KNX DPT 242.600 (DPT_Colour_xyY)."""
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == self.PAYLOAD_LENGTH:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: XYYColor) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(DPTColorXYY.to_knx(value))

    def from_knx(self, payload: DPTArray) -> XYYColor:
        """Convert current payload to value."""
        return DPTColorXYY.from_knx(payload.value)
