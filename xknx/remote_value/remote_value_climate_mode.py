"""
Module for managing an climate mode remote values.

DPT .
"""
from enum import Enum

from xknx.dpt import (
    DPTArray, DPTControllerStatus, DPTHVACContrMode, DPTHVACMode)
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueClimateMode(RemoteValue):
    """Abstraction for remote value of KNX climate modes."""

    class ClimateModeType(Enum):
        """Implemented climate mode types."""

        CONTROLLER_STATUS = DPTControllerStatus
        HVAC_CONTR_MODE = DPTHVACContrMode
        HVAC_MODE = DPTHVACMode

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 sync_state=True,
                 device_name=None,
                 climate_mode_type=None,
                 after_update_cb=None):
        """Initialize remote value of KNX climate mode."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address=group_address,
                         group_address_state=group_address_state,
                         sync_state=sync_state,
                         device_name=device_name,
                         after_update_cb=after_update_cb)
        if not isinstance(climate_mode_type, self.ClimateModeType):
            raise ConversionError("invalid climate mode type", climate_mode_type=climate_mode_type, device_name=device_name)
        self._climate_mode_transcoder = climate_mode_type.value

    def supported_operation_modes(self):
        """Return a list of all supported operation modes."""
        return list(self._climate_mode_transcoder.SUPPORTED_MODES.values())

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 1)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(self._climate_mode_transcoder.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self._climate_mode_transcoder.from_knx(payload.value)
