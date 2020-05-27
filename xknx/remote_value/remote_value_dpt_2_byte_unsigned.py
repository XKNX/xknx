"""
Module for managing a DTP 7001 remote value.

DPT 7.001.
"""
from xknx.dpt import DPT2ByteUnsigned, DPTArray

from .remote_value import RemoteValue


class RemoteValueDpt2ByteUnsigned(RemoteValue):
    """Abstraction for remote value of KNX DPT 7.001."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize remote value of KNX DPT 7.001."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address,
                         group_address_state,
                         device_name=device_name,
                         after_update_cb=after_update_cb)

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
