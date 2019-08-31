"""
Module for managing a DTP Scene Number remote value.

DPT 17.001.
"""
from xknx.dpt import DPTArray, DPTSceneNumber

from .remote_value import RemoteValue


class RemoteValueSceneNumber(RemoteValue):
    """Abstraction for remote value of KNX DPT 17.001 (DPT_Scene_Number)."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize remote value of KNX DPT 17.001 (DPT_Scene_Number)."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address,
                         None,
                         device_name=device_name,
                         after_update_cb=after_update_cb)

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTSceneNumber.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTSceneNumber.from_knx(payload.value)
