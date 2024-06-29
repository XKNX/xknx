"""
Module for managing a remote date and time values.

DPT 10.001, 11.001 and 19.001
"""

from __future__ import annotations

from enum import Enum
import time
from typing import TYPE_CHECKING

from xknx.dpt import DPTDate, DPTDateTime, DPTTime
from xknx.exceptions import ConversionError

from .remote_value import GroupAddressesType, RemoteValue, RVCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class DateTimeType(Enum):
    """Enum class for the date or time value type."""

    DATETIME = DPTDateTime
    DATE = DPTDate
    TIME = DPTTime


class RemoteValueDateTime(RemoteValue[time.struct_time]):
    """Abstraction for remote value of KNX 10.001, 11.001 and 19.001 time and date objects."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        value_type: str = "time",
        device_name: str | None = None,
        feature_name: str = "DateTime",
        after_update_cb: RVCallbackType[time.struct_time] | None = None,
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
