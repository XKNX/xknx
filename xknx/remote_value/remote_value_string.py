"""
Module for managing a remote string value.

DPT 16.000
"""
from xknx.dpt import DPTArray, DPTString

from .remote_value import RemoteValue


class RemoteValueString(RemoteValue):
    """Abstraction for remote value of KNX 16.000 (DPT_String_ASCII)."""

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == DPTString.payload_length)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTString.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTString.from_knx(payload.value)
