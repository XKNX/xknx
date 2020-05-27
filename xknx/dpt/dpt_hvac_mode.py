"""Implementation of different KNX DPT HVAC Operation modes."""

from enum import Enum

from xknx.exceptions import ConversionError, CouldNotParseKNXIP

from .dpt import DPTBase


class HVACOperationMode(Enum):
    """Enum for the different KNX HVAC operation modes."""

    AUTO = "Auto"
    COMFORT = "Comfort"
    STANDBY = "Standby"
    NIGHT = "Night"
    FROST_PROTECTION = "Frost Protection"
    HEAT = "Heat"
    MORNING_WARMUP = "Morning Warmup"
    COOL = "Cool"
    NIGHT_PURGE = "Night Purge"
    PRECOOL = "Precool"
    OFF = "Off"
    TEST = "Test"
    EMERGENCY_HEAT = "Emergency Heat"
    FAN_ONLY = "Fan only"
    FREE_COOL = "Free Cool"
    ICE = "Ice"
    DRY = "Dry"
    NODEM = "NoDem"


class DPTHVACMode(DPTBase):
    """
    Abstraction for KNX HVAC mode.

    DPT 20.102
    """

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)
        if raw[0] == 0x04:
            return HVACOperationMode.FROST_PROTECTION
        if raw[0] == 0x03:
            return HVACOperationMode.NIGHT
        if raw[0] == 0x02:
            return HVACOperationMode.STANDBY
        if raw[0] == 0x01:
            return HVACOperationMode.COMFORT
        if raw[0] == 0x00:
            return HVACOperationMode.AUTO
        raise CouldNotParseKNXIP("Could not parse HVACOperationMode")

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if value == HVACOperationMode.AUTO:
            return (0,)
        if value == HVACOperationMode.COMFORT:
            return (1,)
        if value == HVACOperationMode.STANDBY:
            return (2,)
        if value == HVACOperationMode.NIGHT:
            return (3,)
        if value == HVACOperationMode.FROST_PROTECTION:
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
        if raw[0] & 4 > 0:
            return HVACOperationMode.NIGHT
        if raw[0] & 2 > 0:
            return HVACOperationMode.STANDBY
        if raw[0] & 1 > 0:
            return HVACOperationMode.COMFORT
        raise CouldNotParseKNXIP("Could not parse HVACOperationMode")

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if value == HVACOperationMode.AUTO:
            raise ConversionError("Cant serialize DPTControllerStatus", value=value)
        if value == HVACOperationMode.COMFORT:
            return (0x21,)
        if value == HVACOperationMode.STANDBY:
            return (0x22,)
        if value == HVACOperationMode.NIGHT:
            return (0x24,)
        if value == HVACOperationMode.FROST_PROTECTION:
            return (0x28,)
        raise ConversionError("Could not parse DPTControllerStatus", value=value)
