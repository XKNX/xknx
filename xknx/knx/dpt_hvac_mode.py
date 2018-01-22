"""Implementation of different KNX DPT HVAC Operation modes."""

from enum import Enum

from xknx.exceptions import CouldNotParseKNXIP, ConversionError

from .dpt import DPTBase


class HVACOperationMode(Enum):
    """Enum for the different KNX HVAC operation modes."""

    AUTO = "Auto"
    COMFORT = "Comfort"
    STANDBY = "Standby"
    NIGHT = "Night"
    FROST_PROTECTION = "Frost Protection"


class DPTHVACMode(DPTBase):
    """
    Abstraction for KNX KNX HVAC mod.

    DPT 20.102
    """

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)
        if raw[0] == 0x04:
            return HVACOperationMode.FROST_PROTECTION
        elif raw[0] == 0x03:
            return HVACOperationMode.NIGHT
        elif raw[0] == 0x02:
            return HVACOperationMode.STANDBY
        elif raw[0] == 0x01:
            return HVACOperationMode.COMFORT
        elif raw[0] == 0x00:
            return HVACOperationMode.AUTO
        raise CouldNotParseKNXIP("Could not parse HVACOperationMode")

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if value == HVACOperationMode.AUTO:
            return (0,)
        elif value == HVACOperationMode.COMFORT:
            return (1,)
        elif value == HVACOperationMode.STANDBY:
            return (2,)
        elif value == HVACOperationMode.NIGHT:
            return (3,)
        elif value == HVACOperationMode.FROST_PROTECTION:
            return (4,)
        raise ConversionError("Could not parse HVACOperationMode", value=value)


class DPTControllerStatus(DPTBase):
    """
    Abstraction for KNX HVAC Controller status.

    Non-standardised DP type (in accordance with KNX AN 097/07 rev 3).

    Help needed:
    The values of this type were retrieved by reverse engineering. Any
    notes on the correct implementation of this type are highly appreciated.
    """

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)
        if raw[0] & 8 > 0:
            return HVACOperationMode.FROST_PROTECTION
        elif raw[0] & 4 > 0:
            return HVACOperationMode.NIGHT
        elif raw[0] & 2 > 0:
            return HVACOperationMode.STANDBY
        elif raw[0] & 1 > 0:
            return HVACOperationMode.COMFORT
        raise CouldNotParseKNXIP("Could not parse HVACOperationMode")

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if value == HVACOperationMode.AUTO:
            raise ConversionError("Cant serialize DPTControllerStatus", value=value)
        elif value == HVACOperationMode.COMFORT:
            return (0x21,)
        elif value == HVACOperationMode.STANDBY:
            return (0x22,)
        elif value == HVACOperationMode.NIGHT:
            return (0x24,)
        elif value == HVACOperationMode.FROST_PROTECTION:
            return (0x28,)
        raise ConversionError("Could not parse HVACOperationMode", value=value)
