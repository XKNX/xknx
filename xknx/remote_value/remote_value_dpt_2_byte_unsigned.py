"""
Module for managing a DTP 7001 remote value.

DPT 7.001.
"""
from xknx.dpt import DPT2ByteUnsigned, DPTArray

from .remote_value import RemoteValue


class RemoteValueDpt2ByteUnsigned(RemoteValue):
    """Abstraction for remote value of KNX DPT 7.001."""

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 2)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPT2ByteUnsigned.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPT2ByteUnsigned.from_knx(payload.value)
