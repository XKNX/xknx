"""
Module for managing a remote temperature value.

DPT 9.001.
"""
from xknx.knx import DPTArray, DPTTemperature

from .remote_value import RemoteValue


class RemoteValueTemp(RemoteValue):
    """Abstraction for remote value of KNX 9.001 (DPT_Value_Temp)."""

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 2)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTTemperature.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTTemperature.from_knx(payload.value)
