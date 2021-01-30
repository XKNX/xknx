"""
Module for managing a remote temperature value.

DPT 9.001.
"""
from xknx.dpt import DPTArray, DPTTemperature

from .remote_value import RemoteValue


class RemoteValueTemp(RemoteValue[DPTArray]):
    """Abstraction for remote value of KNX 9.001 (DPT_Value_Temp)."""

    # pylint: disable=no-self-use

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (
            payload
            if isinstance(payload, DPTArray) and len(payload.value) == 2
            else None
        )

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTTemperature.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTTemperature.from_knx(payload.value)
