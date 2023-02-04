"""
Module for managing an RGBW remote value.

DPT 251.600.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueColorRGBW(RemoteValue[DPTArray, tuple[int, int, int, int]]):
    """Abstraction for remote value of KNX DPT 251.600 (DPT_Color_RGBW)."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Color RGBW",
        after_update_cb: AsyncCallbackType | None = None,
    ):
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
        self.previous_value: tuple[int, int, int, int] = (0, 0, 0, 0)

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray) and len(payload.value) == 6:
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: Sequence[int]) -> DPTArray:
        """
        Convert value (4-6 bytes) to payload (6 bytes).

        * Structure of DPT 251.600
        ** Byte 0: R value
        ** Byte 1: G value
        ** Byte 2: B value
        ** Byte 3: W value
        ** Byte 4: 0x00 (reserved)
        ** Byte 5:
        *** Bit 0: W value valid?
        *** Bit 1: B value valid?
        *** Bit 2: G value valid?
        *** Bit 3: R value valid?
        *** Bit 4-7: 0

        In case we receive
        * > 6 bytes: error
        * 6 bytes: all bytes are passed through
        * 5 bytes: 0x00?? fill up to 6 bytes
        * 4 bytes: 0x000f right padding to 6 bytes
        * < 4 bytes: error
        """
        if not isinstance(value, (list, tuple)):
            raise ConversionError(
                "Could not serialize RemoteValueColorRGBW (wrong type, expecting list of 4-6 bytes))",
                value=value,
                type=type(value),
            )
        if not 4 <= len(value) <= 6:
            raise ConversionError(
                "Could not serialize value to DPT 251.600 (wrong length, expecting list of 4-6 bytes)",
                value=value,
                type=type(value),
            )
        rgbw = value[:4]
        if (
            any(not isinstance(color, int) for color in rgbw)
            or any(color < 0 for color in rgbw)
            or any(color > 255 for color in rgbw)
        ):
            raise ConversionError(
                "Could not serialize DPT 251.600 (wrong RGBW values)", value=value
            )
        if len(value) < 5:
            return DPTArray(list(rgbw) + [0x00, 0x0F])
        if len(value) < 6:
            return DPTArray(list(rgbw) + [0x00] + list(value[4:]))
        return DPTArray(value)

    def from_knx(self, payload: DPTArray) -> tuple[int, int, int, int]:
        """
        Convert current payload to value. Always 4 byte (RGBW).

        If one element is invalid, use the previous value. All previous element
        values are initialized to 0.
        """
        _result = list(self.previous_value)
        for i in range(len(payload.value) - 2):
            if payload.value[5] & (0x08 >> i):  # R,G,B,W value valid?
                _result[i] = payload.value[i]
        result = (_result[0], _result[1], _result[2], _result[3])
        self.previous_value = result
        return result
