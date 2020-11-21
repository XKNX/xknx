"""
Module for managing a control remote value.

Examples are switching commands with priority control, relative dimming or blinds control commands.
DPT 2.yyy and DPT 3.yyy
"""
from xknx.dpt import (
    DPTBinary,
    DPTControl,
    DPTControlStartStop,
    DPTControlStartStopBlinds,
    DPTControlStartStopDimming,
    DPTControlStepwise,
    DPTControlStepwiseBlinds,
    DPTControlStepwiseDimming,
)
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueControl(RemoteValue):
    """Abstraction for remote value used for controling."""

    DPTMAP = {
        "control": DPTControl,
        "startstop": DPTControlStartStop,
        "startstop_dimming": DPTControlStartStopDimming,
        "startstop_blinds": DPTControlStartStopBlinds,
        "stepwise": DPTControlStepwise,
        "stepwise_dimming": DPTControlStepwiseDimming,
        "stepwise_blinds": DPTControlStepwiseBlinds,
    }

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        value_type=None,
        device_name=None,
        after_update_cb=None,
        invert=False,
    ):
        """Initialize control remote value."""
        # pylint: disable=too-many-arguments
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            device_name=device_name,
            after_update_cb=after_update_cb,
        )
        self.invert = invert
        if value_type not in self.DPTMAP:
            raise ConversionError(
                "invalid value type", value_type=value_type, device_name=device_name
            )
        self.value_type = value_type

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTBinary(self.DPTMAP[self.value_type].to_knx(value, invert=self.invert))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self.DPTMAP[self.value_type].from_knx(payload.value, invert=self.invert)
