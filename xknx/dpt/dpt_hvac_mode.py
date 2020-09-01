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


class _DPTClimateMode(DPTBase):
    """Base class for KNX Climate modes."""

    SUPPORTED_MODES = {}

    payload_length = 1

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        if raw[0] in cls.SUPPORTED_MODES:
            return cls.SUPPORTED_MODES[raw[0]]
        raise CouldNotParseKNXIP("Could not parse HVACOperationMode")

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        for knx_value, mode in cls.SUPPORTED_MODES.items():
            if mode == value:
                return (knx_value,)
        raise ConversionError("Could not parse %s" % cls.__name__, value=value)


class DPTHVACContrMode(_DPTClimateMode):
    """
    Abstraction for KNX HVAC controller mode.

    DPT 20.105
    """

    SUPPORTED_MODES = {
        0: HVACOperationMode.AUTO,
        1: HVACOperationMode.HEAT,
        2: HVACOperationMode.MORNING_WARMUP,
        3: HVACOperationMode.COOL,
        4: HVACOperationMode.NIGHT_PURGE,
        5: HVACOperationMode.PRECOOL,
        6: HVACOperationMode.OFF,
        7: HVACOperationMode.TEST,
        8: HVACOperationMode.EMERGENCY_HEAT,
        9: HVACOperationMode.FAN_ONLY,
        10: HVACOperationMode.FREE_COOL,
        11: HVACOperationMode.ICE,
        14: HVACOperationMode.DRY,
        20: HVACOperationMode.NODEM,
    }


class DPTHVACMode(_DPTClimateMode):
    """
    Abstraction for KNX HVAC mode.

    DPT 20.102
    """

    SUPPORTED_MODES = {
        0: HVACOperationMode.AUTO,
        1: HVACOperationMode.COMFORT,
        2: HVACOperationMode.STANDBY,
        3: HVACOperationMode.NIGHT,
        4: HVACOperationMode.FROST_PROTECTION,
    }
    SUPPORTED_MODES_INV = dict(reversed(item) for item in SUPPORTED_MODES.items())


class DPTControllerStatus(_DPTClimateMode):
    """
    Abstraction for KNX HVAC Controller status.

    Non-standardised DP type (in accordance with KNX AN 097/07 rev 3).

    Help needed:
    The values of this type were retrieved by reverse engineering. Any
    notes on the correct implementation of this type are highly appreciated.
    """

    SUPPORTED_MODES = {
        0x21: HVACOperationMode.COMFORT,
        0x22: HVACOperationMode.STANDBY,
        0x24: HVACOperationMode.NIGHT,
        0x28: HVACOperationMode.FROST_PROTECTION,
    }

    SUPPORTED_MODES_INV = dict(reversed(item) for item in SUPPORTED_MODES.items())

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        if raw[0] & 8 > 0:
            return HVACOperationMode.FROST_PROTECTION
        if raw[0] & 4 > 0:
            return HVACOperationMode.NIGHT
        if raw[0] & 2 > 0:
            return HVACOperationMode.STANDBY
        if raw[0] & 1 > 0:
            return HVACOperationMode.COMFORT
        raise CouldNotParseKNXIP("Could not parse HVACOperationMode")
