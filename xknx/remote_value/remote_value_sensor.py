"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Union

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.exceptions import ConversionError

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueSensor(RemoteValue[DPTArray, Union[int, float, str]]):
    """Abstraction for many different sensor DPT types."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool = True,
        value_type: int | str | None = None,
        device_name: str | None = None,
        feature_name: str = "Value",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize RemoteValueSensor class."""
        if value_type is None:
            raise ConversionError("no value type given", device_name=device_name)
        _dpt_class = DPTBase.parse_transcoder(value_type)
        if _dpt_class is None:
            raise ConversionError(
                "invalid value type", value_type=value_type, device_name=device_name
            )
        self.dpt_class = _dpt_class
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray | None:
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray)
            and len(payload.value) == self.dpt_class.payload_length
            else None
        )

    def to_knx(self, value: int | float | str) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(self.dpt_class.to_knx(value))

    def from_knx(self, payload: DPTArray) -> int | float | str:
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)  # type: ignore

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.dpt_class.unit

    @property
    def ha_device_class(self) -> str | None:
        """Return a string representing the home assistant device class."""
        return getattr(self.dpt_class, "ha_device_class", None)  # type: ignore
