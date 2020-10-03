"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from xknx.dpt import DPTArray, DPTBase
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueSensor(RemoteValue):
    """Abstraction for many different sensor DPT types."""

    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        sync_state=True,
        value_type=None,
        device_name=None,
        feature_name="Value",
        after_update_cb=None,
    ):
        """Initialize RemoteValueSensor class."""
        # pylint: disable=too-many-arguments
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
        )

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (
            isinstance(payload, DPTArray)
            and len(payload.value) == self.dpt_class.payload_length
        )

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(self.dpt_class.to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self.dpt_class.from_knx(payload.value)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.dpt_class.unit

    @property
    def ha_device_class(self):
        """Return a string representing the home assistant device class."""
        return getattr(self.dpt_class, "ha_device_class", None)
