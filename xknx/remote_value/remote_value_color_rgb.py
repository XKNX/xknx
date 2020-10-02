"""
Module for managing an RGB remote value.

DPT 232.600.
"""
from typing import List

from xknx.dpt import DPTArray
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueColorRGB(RemoteValue):
    """Abstraction for remote value of KNX DPT 232.600 (DPT_Color_RGB)."""

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        device_name=None,
        feature_name="Color RGB",
        after_update_cb=None,
        passive_group_addresses: List[str] = None,
    ):
        """Initialize remote value of KNX DPT 232.600 (DPT_Color_RGB)."""
        # pylint: disable=too-many-arguments
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
            passive_group_addresses=passive_group_addresses,
        )

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTArray) and len(payload.value) == 3

    def to_knx(self, value):
        """Convert value to payload."""
        if not isinstance(value, (list, tuple)):
            raise ConversionError(
                "Could not serialize RemoteValueColorRGB (wrong type)",
                value=value,
                type=type(value),
            )
        if len(value) != 3:
            raise ConversionError(
                "Could not serialize DPT 232.600 (wrong length)",
                value=value,
                type=type(value),
            )
        if (
            any(not isinstance(color, int) for color in value)
            or any(color < 0 for color in value)
            or any(color > 255 for color in value)
        ):
            raise ConversionError(
                "Could not serialize DPT 232.600 (wrong bytes)", value=value
            )

        return DPTArray(list(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return payload.value[0], payload.value[1], payload.value[2]
