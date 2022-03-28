"""Implementation of different KNX DPT HVAC Operation modes."""
from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from xknx.exceptions import ConversionError

from .dpt import DPTBase

HVACModeT = TypeVar("HVACModeT", "HVACControllerMode", "HVACOperationMode")


class HVACOperationMode(Enum):
    """Enum for the different KNX HVAC operation modes."""

    AUTO = "Auto"
    COMFORT = "Comfort"
    STANDBY = "Standby"
    NIGHT = "Night"
    FROST_PROTECTION = "Frost Protection"


class HVACControllerMode(Enum):
    """Enum for the different KNX HVAC controller modes."""

    AUTO = "Auto"
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


class _DPTClimateMode(DPTBase, Generic[HVACModeT]):
    """Base class for KNX Climate modes."""

    SUPPORTED_MODES: dict[int, HVACModeT] = {}

    payload_length = 1

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> HVACModeT:
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw)
        try:
            return cls.SUPPORTED_MODES[raw[0]]
        except KeyError:
            raise ConversionError(f"Payload not supported for {cls.__name__}", raw=raw)

    @classmethod
    def to_knx(cls, value: HVACModeT) -> tuple[int]:
        """Serialize to KNX/IP raw data."""
        for knx_value, mode in cls.SUPPORTED_MODES.items():
            if mode == value:
                return (knx_value,)
        raise ConversionError(f"Value not supported for {cls.__name__}", value=value)


class DPTHVACContrMode(_DPTClimateMode[HVACControllerMode]):
    """
    Abstraction for KNX HVAC controller mode.

    DPT 20.105
    """

    SUPPORTED_MODES: dict[int, HVACControllerMode] = {
        0: HVACControllerMode.AUTO,
        1: HVACControllerMode.HEAT,
        2: HVACControllerMode.MORNING_WARMUP,
        3: HVACControllerMode.COOL,
        4: HVACControllerMode.NIGHT_PURGE,
        5: HVACControllerMode.PRECOOL,
        6: HVACControllerMode.OFF,
        7: HVACControllerMode.TEST,
        8: HVACControllerMode.EMERGENCY_HEAT,
        9: HVACControllerMode.FAN_ONLY,
        10: HVACControllerMode.FREE_COOL,
        11: HVACControllerMode.ICE,
        14: HVACControllerMode.DRY,
        20: HVACControllerMode.NODEM,
    }


class DPTHVACMode(_DPTClimateMode[HVACOperationMode]):
    """
    Abstraction for KNX HVAC mode.

    DPT 20.102
    """

    SUPPORTED_MODES: dict[int, HVACOperationMode] = {
        0: HVACOperationMode.AUTO,
        1: HVACOperationMode.COMFORT,
        2: HVACOperationMode.STANDBY,
        3: HVACOperationMode.NIGHT,
        4: HVACOperationMode.FROST_PROTECTION,
    }


class DPTControllerStatus(_DPTClimateMode[HVACOperationMode]):
    """
    Abstraction for KNX HVAC Controller status.

    Non-standardised DP type (in accordance with KNX AN 097/07 rev 3).

    Help needed:
    The values of this type were retrieved by reverse engineering. Any
    notes on the correct implementation of this type are highly appreciated.
    """

    SUPPORTED_MODES: dict[int, HVACOperationMode] = {
        0x21: HVACOperationMode.COMFORT,
        0x22: HVACOperationMode.STANDBY,
        0x24: HVACOperationMode.NIGHT,
        0x28: HVACOperationMode.FROST_PROTECTION,
    }

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> HVACOperationMode:
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
        raise ConversionError(f"Payload not supported for {cls.__name__}", raw=raw)
