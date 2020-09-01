"""
Module for managing a DTP Scene Number remote value.

DPT 17.001.
"""
from xknx.dpt import DPTArray, DPTSceneNumber

from .remote_value import RemoteValue


class RemoteValueSceneNumber(RemoteValue):
    """Abstraction for remote value of KNX DPT 17.001 (DPT_Scene_Number)."""

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTArray) and len(payload.value) == 1

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTSceneNumber.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTSceneNumber.from_knx(payload.value)
