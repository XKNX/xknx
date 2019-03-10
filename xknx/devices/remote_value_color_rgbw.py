"""
Module for managing an RGBW remote value.

DPT 251.600.
"""
from xknx.exceptions import ConversionError
from xknx.knx import DPTArray

from .remote_value import RemoteValue


class RemoteValueColorRGBW(RemoteValue):
    """Abstraction for remote value of KNX DPT 251.600 (DPT_Color_RGBW)."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize remote value of KNX DPT 251.600 (DPT_Color_RGBW)."""
        # pylint: disable=too-many-arguments
        super(RemoteValueColorRGBW, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 6)

    def to_knx(self, value):
        """
        Convert value (4-6 bytes) to payload (6 bytes).

        * Structure of DPT 251.600
        ** Bytes 0, 1:
        *** Bit 0-11: 0
        *** Bit 12,13,14,15: R,G,B,W value valid?
        ** Byte 2: R value
        ** Byte 3: G value
        ** Byte 4: B value
        ** Byte 5: W value

        In case we receive
        * > 6 bytes: error
        * 6 bytes: all bytes are passed through
        * 5 bytes: 0x00 left padding
        * 4 bytes: 0x000f left padding
        * < 4 bytes: error
        """
        if not isinstance(value, (list, tuple)):
            raise ConversionError("Cannot serialize RemoteValueColorRGBW (wrong type, expecting list of 4-6 bytes))",
                                  value=value, type=type(value))
        if len(value) < 4 or len(value) > 6:
            raise ConversionError("Cannot serialize value to DPT 251.600 (wrong length, expecting list of 4-6 bytes)",
                                  value=value, type=type(value))
        rgbw = value[len(value)-4:]
        if any(not isinstance(color, int) for color in rgbw) \
                or any(color < 0 for color in rgbw) \
                or any(color > 255 for color in rgbw):
            raise ConversionError("Cant serialize DPT 251.600 (wrong RGBW values)", value=value)
        return DPTArray([0x00, 0x0f][:6-len(value)] + list(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return payload.value[0:6]
