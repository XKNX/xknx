"""
Module for managing a control remote value.

Examples are switching commands with priority control, relative dimming or blinds control commands.
DPT 2.yyy and DPT 3.yyy
"""
from typing import List, Optional

from xknx.dpt import DPTBase, DPTBinary
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueControl(RemoteValue):
    """Abstraction for remote value used for controling."""

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        sync_state=True,
        value_type=None,
        device_name=None,
        feature_name="Control",
        after_update_cb=None,
        invert=False,
        passive_group_addresses: List[str] = None,
    ):
        """Initialize control remote value."""
        # pylint: disable=too-many-arguments
        self.invert = invert
        _dpt_class = DPTBase.parse_transcoder(value_type)
        if _dpt_class is None:
            raise ConversionError(
                "invalid value type", value_type=value_type, device_name=device_name
            )
        self.dpt_class = _dpt_class
        super().__init__(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            device_name=device_name,
            feature_name=feature_name,
            after_update_cb=after_update_cb,
            passive_group_addresses=passive_group_addresses,
        )

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return isinstance(payload, DPTBinary)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTBinary(self.dpt_class.to_knx(value, invert=self.invert))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value, invert=self.invert)

    @property
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        return self.dpt_class.unit

    @property
    def ha_device_class(self) -> Optional[str]:
        """Return a string representing the home assistant device class."""
        return getattr(self.dpt_class, "ha_device_class", None)
