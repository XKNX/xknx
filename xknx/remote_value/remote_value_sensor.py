"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, TypeVar, Union

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTNumeric, DPTString
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX

ValueT = TypeVar("ValueT")


class _RemoteValueGeneric(RemoteValue[DPTArray, ValueT]):
    """Abstraction for generic DPT types."""

    dpt_base_class: type[DPTBase]
    _default_dpt_class: type[DPTBase] | None = None

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        value_type: int | str | None = None,
        device_name: str | None = None,
        feature_name: str = "Value",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize RemoteValueSensor class."""
        _dpt_class = (
            self.dpt_base_class.parse_transcoder(value_type)
            if value_type is not None
            else self._default_dpt_class
        )
        if _dpt_class is None:
            raise ConversionError(
                f"invalid value type for base class {self.dpt_base_class.__name__}",
                value_type=value_type,
                device_name=device_name,
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

    def payload_valid(self, payload: DPTArray | DPTBinary | None) -> DPTArray:
        """Test if telegram payload may be parsed."""
        if (
            isinstance(payload, DPTArray)
            and len(payload.value) == self.dpt_class.payload_length
        ):
            return payload
        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))

    def to_knx(self, value: ValueT) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(self.dpt_class.to_knx(value))

    @abstractmethod
    def from_knx(self, payload: DPTArray) -> ValueT:
        """Convert current payload to value."""

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.dpt_class.unit

    @property
    def ha_device_class(self) -> str | None:
        """Return a string representing the home assistant device class."""
        return getattr(self.dpt_class, "ha_device_class", None)


class RemoteValueSensor(_RemoteValueGeneric[Union[int, float, str]]):
    """Abstraction for sensor DPT types."""

    dpt_base_class = DPTBase
    dpt_class: type[DPTBase]

    def from_knx(self, payload: DPTArray) -> int | float | str:
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)  # type: ignore


class RemoteValueNumeric(_RemoteValueGeneric[Union[int, float]]):
    """Abstraction for numeric DPT types."""

    dpt_base_class = DPTNumeric
    dpt_class: type[DPTNumeric]

    def from_knx(self, payload: DPTArray) -> int | float:
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)


class RemoteValueString(_RemoteValueGeneric[str]):
    """Abstraction for string DPT types."""

    dpt_base_class = DPTString
    dpt_class: type[DPTString]
    _default_dpt_class = DPTString

    def from_knx(self, payload: DPTArray) -> str:
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)
