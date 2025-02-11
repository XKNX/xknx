"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from xknx.dpt import DPTBase, DPTNumeric, DPTString
from xknx.exceptions import ConversionError
from xknx.typing import DPTParsable

from .remote_value import GroupAddressesType, RemoteValue, RVCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX

ValueT = TypeVar("ValueT")


class _RemoteValueGeneric(RemoteValue[ValueT]):
    """Abstraction for generic DPT types."""

    dpt_base_class: type[DPTBase]
    _default_dpt_class: type[DPTBase] | None = None
    dpt_class: type[DPTBase]

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        value_type: DPTParsable | type[DPTBase] | None = None,
        device_name: str | None = None,
        feature_name: str = "Value",
        after_update_cb: RVCallbackType[ValueT] | None = None,
    ) -> None:
        """Initialize RemoteValueSensor class."""
        try:
            if value_type is None:
                if self._default_dpt_class is None:
                    raise ValueError
                self.dpt_class = self._default_dpt_class
            else:
                self.dpt_class = self.dpt_base_class.get_dpt(value_type)
        except ValueError:
            raise ConversionError(
                f"invalid value type for base class {self.dpt_base_class.dpt_name()}",
                value_type=value_type,
                device_name=device_name,
            ) from None
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.dpt_class.unit

    @property
    def ha_device_class(self) -> str | None:
        """Return a string representing the home assistant device class."""
        return getattr(self.dpt_class, "ha_device_class", None)


class RemoteValueSensor(_RemoteValueGeneric[int | float | str]):
    """Abstraction for sensor DPT types."""

    dpt_base_class = DPTBase
    dpt_class: type[DPTBase]


class RemoteValueNumeric(_RemoteValueGeneric[int | float]):
    """Abstraction for numeric DPT types."""

    dpt_base_class = DPTNumeric
    dpt_class: type[DPTNumeric]


class RemoteValueString(_RemoteValueGeneric[str]):
    """Abstraction for string DPT types."""

    dpt_base_class = DPTString
    dpt_class: type[DPTString]
    _default_dpt_class = DPTString
