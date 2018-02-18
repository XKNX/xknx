"""
Module for managing a DTP 5010 remote value.

DPT 5.010.
"""
from xknx.knx import DPTArray, DPTValue1Ucount

from .remote_value import RemoteValue


class RemoteValueDptValue1Ucount(RemoteValue):
    """Abstraction for remote value of KNX DPT 5.010."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize remote value of KNX DPT 5.010."""
        # pylint: disable=too-many-arguments
        super(RemoteValueDptValue1Ucount, self).__init__(
            xknx, group_address, None,
            device_name=device_name, after_update_cb=after_update_cb)

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(DPTValue1Ucount.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return DPTValue1Ucount.from_knx(payload.value)
