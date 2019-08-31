"""
Module for managing an 1 count remote value.

DPT 6.010.
"""
from xknx.knx import DPTArray, DPTValue1Count

from .remote_value import RemoteValue


class RemoteValue1Count(RemoteValue):
    """Abstraction for remote value of KNX 6.010 (DPT_Value_1_Count)."""

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTValue1Count.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTValue1Count.from_knx(payload.value)
