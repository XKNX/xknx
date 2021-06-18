"""
Module for managing a remote date and time values.

DPT 10.001, 11.001 and 19.001
"""
from __future__ import annotations

from enum import Enum
import time
from typing import TYPE_CHECKING

from xknx.dpt import DPTArray, DPTBinary, DPTDate, DPTDateTime, DPTTime
from xknx.exceptions import ConversionError

from .remote_value import AsyncCallbackType, GroupAddressesType, RemoteValue

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class DateTimeType(Enum):
    """Enum class for the date or time value type."""

    DATETIME = DPTDateTime
    DATE = DPTDate
    TIME = DPTTime


class RemoteValueDateTime(RemoteValue[DPTArray, time.struct_time]):
    """Abstraction for remote value of KNX 10.001, 11.001 and 19.001 time and date objects."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        value_type: str = "time",
        device_name: str | None = None,
        feature_name: str = "DateTime",
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize RemoteValueDateTime class."""
        try:
            self.dpt_class: type[DPTDate | DPTDateTime | DPTTime] = DateTimeType[
                value_type.upper()
            ].value
        except KeyError:
            raise ConversionError(
                "invalid datetime value type",
                value_type=value_type,
                device_name=device_name,
                feature_name=feature_name,
            )
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

    def to_knx(self, value: time.struct_time) -> DPTArray:
        """Convert value to payload."""
        return DPTArray(self.dpt_class.to_knx(value))

    def from_knx(self, payload: DPTArray) -> time.struct_time:
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)
