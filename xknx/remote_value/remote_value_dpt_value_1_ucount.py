"""
Module for managing a DTP 5010 remote value.

DPT 5.010.
"""
from xknx.dpt import DPTArray, DPTValue1Ucount

from .remote_value import RemoteValue


class RemoteValueDptValue1Ucount(RemoteValue[DPTArray]):
    """Abstraction for remote value of KNX DPT 5.010."""

    # pylint: disable=no-self-use

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 1
            else None
        )

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTValue1Ucount.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTValue1Ucount.from_knx(payload.value)
