"""
Module for managing a remote date and time values.

DPT 10.001, 11.001 and 19.001
"""
from enum import Enum
import time
from typing import TYPE_CHECKING, List, Optional, Type, Union

from xknx.dpt import DPTArray, DPTBinary, DPTDate, DPTDateTime, DPTTime
from xknx.exceptions import ConversionError

from .remote_value import AsyncCallbackType, RemoteValue

if TYPE_CHECKING:
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX


class DateTimeType(Enum):
    """Enum class for the date or time value type."""

    DATETIME = DPTDateTime
    DATE = DPTDate
    TIME = DPTTime


class RemoteValueDateTime(RemoteValue[DPTArray]):
    """Abstraction for remote value of KNX 10.001, 11.001 and 19.001 time and date objects."""

    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        sync_state: bool = True,
        value_type: str = "time",
        device_name: Optional[str] = None,
        feature_name: str = "DateTime",
        after_update_cb: Optional[AsyncCallbackType] = None,
        passive_group_addresses: Optional[List["GroupAddressableType"]] = None,
    ):
        """Initialize RemoteValueSensor class."""
        # pylint: disable=too-many-arguments
        try:
            self.dpt_class: Type[Union[DPTDate, DPTDateTime, DPTTime]] = DateTimeType[
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
            passive_group_addresses=passive_group_addresses,
        )

    def payload_valid(
        self, payload: Optional[Union[DPTArray, DPTBinary]]
    ) -> Optional[DPTArray]:
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
