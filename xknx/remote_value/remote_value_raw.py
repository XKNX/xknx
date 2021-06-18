"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Union

from xknx.dpt.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueRaw(RemoteValue[Union[DPTArray, DPTBinary], int]):
    """Abstraction for raw values."""

    def __init__(
        self,
        xknx: XKNX,
        payload_length: int,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str = "Raw",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize RemoteValueSensor class."""
        self.payload_length = payload_length
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def payload_valid(
        self, payload: DPTArray | DPTBinary | None
    ) -> DPTArray | DPTBinary | None:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTBinary) and self.payload_length == 0:
            return payload
        if isinstance(payload, DPTArray) and len(payload.value) == self.payload_length:
            return payload
        return None

    def to_knx(self, value: int) -> DPTArray | DPTBinary:
        """Convert value to payload."""
        if self.payload_length == 0:
            try:
                return DPTBinary(value)
            except TypeError as err:
                raise ConversionError(
                    "Could not init DPTBinary", value=str(value)
                ) from err
        try:
            return DPTArray(value.to_bytes(length=self.payload_length, byteorder="big"))
        except (AttributeError, OverflowError) as err:
            raise ConversionError("Could not init DPTArray", value=str(value)) from err

    def from_knx(self, payload: DPTArray | DPTBinary) -> int:
        """Convert current payload to value."""
        if isinstance(payload, DPTBinary):
            return payload.value
        try:
            return int.from_bytes(payload.value, byteorder="big")
        except ValueError as err:
            raise ConversionError("Could not parse payload", payload=payload) from err
