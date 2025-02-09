"""Module for managing remote value with payload length based DPT detection."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary, DPTNumeric
from xknx.exceptions import ConversionError, CouldNotParseTelegram

from .remote_value import GroupAddressesType, RemoteValue, RVCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class RemoteValueByLength(RemoteValue[float]):
    """RemoteValue with DPT detection based on payload length of first received value."""

    def __init__(
        self,
        xknx: XKNX,
        dpt_classes: Iterable[type[DPTNumeric]],
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str | None = None,
        after_update_cb: RVCallbackType[float] | None = None,
    ) -> None:
        """Initialize RemoteValueByLength class."""
        _payload_lengths = set()
        for dpt_class in dpt_classes:
            if (
                not issubclass(dpt_class, DPTNumeric)
                or dpt_class.payload_type is not DPTArray
            ):
                raise ConversionError(
                    "Only DPTNumeric subclasses with payload_type DPTArray are supported"
                )
            if dpt_class.payload_length in _payload_lengths:
                raise ConversionError(
                    f"Duplicate payload_length {dpt_class.payload_length} in {dpt_classes}"
                )
            _payload_lengths.add(dpt_class.payload_length)

        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
        )

        self._dpt_classes = dpt_classes
        self._internal_dpt_class: type[DPTNumeric] | None = None

    def to_knx(self, value: float) -> DPTArray:
        """Convert value to payload."""
        if self._internal_dpt_class is None:
            raise ConversionError(
                f"RemoteValue DPT not initialized for {self.device_name}"
            )
        return self._internal_dpt_class.to_knx(value)

    def from_knx(self, payload: DPTArray | DPTBinary) -> float:
        """Convert current payload to value."""
        if self._internal_dpt_class is None:
            self._internal_dpt_class = self._determine_dpt_class(payload)

        return self._internal_dpt_class.from_knx(payload)

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        if not self._internal_dpt_class:
            return None
        return self._internal_dpt_class.unit

    @property
    def ha_device_class(self) -> str | None:
        """Return a string representing the home assistant device class."""
        if not self._internal_dpt_class:
            return None
        return getattr(self._internal_dpt_class, "ha_device_class", None)

    def _determine_dpt_class(self, payload: DPTArray | DPTBinary) -> type[DPTNumeric]:
        """Test if telegram payload may be parsed."""
        if isinstance(payload, DPTArray):
            try:
                return next(
                    dpt_class
                    for dpt_class in self._dpt_classes
                    if dpt_class.payload_type is DPTArray
                    and dpt_class.payload_length == len(payload.value)
                )
            except StopIteration:
                pass

        raise CouldNotParseTelegram("Payload invalid", payload=str(payload))
