"""
Module for managing an RGBW remote value.

DPT 251.600.
"""
from xknx.dpt import DPTArray
from xknx.exceptions import ConversionError

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
        self.previous_value = (0, 0, 0, 0)

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (isinstance(payload, DPTArray)
                and len(payload.value) == 6)

    def to_knx(self, value):
        """
        Convert value (4-6 bytes) to payload (6 bytes).

        * Structure of DPT 251.600
        ** Byte 0: R value
        ** Byte 1: G value
        ** Byte 2: B value
        ** Byte 3: W value
        ** Byte 4: 0x00 (reserved)
        ** Byte 5:
        *** Bit 0: W value valid?
        *** Bit 1: B value valid?
        *** Bit 2: G value valid?
        *** Bit 3: R value valid?
        *** Bit 4-7: 0

        In case we receive
        * > 6 bytes: error
        * 6 bytes: all bytes are passed through
        * 5 bytes: 0x00?? fill up to 6 bytes
        * 4 bytes: 0x000f right padding to 6 bytes
        * < 4 bytes: error
        """
        if not isinstance(value, (list, tuple)):
            raise ConversionError("Cannot serialize RemoteValueColorRGBW (wrong type, expecting list of 4-6 bytes))",
                                  value=value, type=type(value))
        if len(value) < 4 or len(value) > 6:
            raise ConversionError("Cannot serialize value to DPT 251.600 (wrong length, expecting list of 4-6 bytes)",
                                  value=value, type=type(value))
        rgbw = value[:4]
        if any(not isinstance(color, int) for color in rgbw) \
                or any(color < 0 for color in rgbw) \
                or any(color > 255 for color in rgbw):
            raise ConversionError("Cannot serialize DPT 251.600 (wrong RGBW values)", value=value)
        if len(value) < 5:
            return DPTArray(list(rgbw) + [0x00, 0x0f])
        if len(value) < 6:
            return DPTArray(list(rgbw) + [0x00] + list(value[4:]))
        return DPTArray(value)

    def from_knx(self, payload):
        """
        Convert current payload to value. Always 4 byte (RGBW).

        If one element is invalid, use the previous value. All previous element
        values are initialized to 0.
        """
        result = []
        for i in range(0, len(payload.value) - 2):
            valid = (payload.value[5] & (0x08 >> i)) != 0  # R,G,B,W value valid?
            result.append(payload.value[i] if valid else self.previous_value[i])
        self.previous_value = result
        return result
