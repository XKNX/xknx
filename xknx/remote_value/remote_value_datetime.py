"""
Module for managing a remote date and time values.

DPT 10.001, 11.001 and 19.001
"""
from enum import Enum
import time
from typing import List

from xknx.dpt import DPTArray, DPTDate, DPTDateTime, DPTTime
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class DateTimeType(Enum):
    """Enum class for the date or time value type."""

    DATETIME = DPTDateTime
    DATE = DPTDate
    TIME = DPTTime


class RemoteValueDateTime(RemoteValue):
    """Abstraction for remote value of KNX 10.001, 11.001 and 19.001 time and date objects."""

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        sync_state=True,
        value_type="time",
        device_name=None,
        feature_name="DateTime",
        after_update_cb=None,
        passive_group_addresses: List[str] = None,
    ):
        """Initialize RemoteValueSensor class."""
        # pylint: disable=too-many-arguments
        try:
            self.dpt_class = DateTimeType[value_type.upper()].value
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

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (
            isinstance(payload, DPTArray)
            and len(payload.value) == self.dpt_class.payload_length
        )

    def to_knx(self, value: time.struct_time):
        """Convert value to payload."""
        return DPTArray(self.dpt_class.to_knx(value))

    def from_knx(self, payload) -> time.struct_time:
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)
