"""Implementation of different KNX DPT HVAC Operation modes."""

from __future__ import annotations

from enum import Enum

from xknx.exceptions import ConversionError

from .dpt import DPTEnum
from .payload import DPTArray, DPTBinary


# ruff: noqa: RUF012  # Mutable class attributes should be annotated with `typing.ClassVar`
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


class DPTHVACContrMode(DPTEnum[HVACControllerMode]):
    """
    Abstraction for KNX HVAC controller mode.

    DPT 20.105
    """

    dpt_main_number = 20
    dpt_sub_number = 105
    value_type = "hvac_controller_mode"
    data_type = HVACControllerMode
    VALUE_MAP = {
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


class DPTHVACMode(DPTEnum[HVACOperationMode]):
    """
    Abstraction for KNX HVAC mode.

    DPT 20.102
    """

    dpt_main_number = 20
    dpt_sub_number = 102
    value_type = "hvac_mode"
    data_type = HVACOperationMode
    VALUE_MAP = {
        0: HVACOperationMode.AUTO,
        1: HVACOperationMode.COMFORT,
        2: HVACOperationMode.STANDBY,
        3: HVACOperationMode.NIGHT,
        4: HVACOperationMode.FROST_PROTECTION,
    }


class DPTControllerStatus(DPTEnum[HVACOperationMode]):
    """
    Abstraction for KNX HVAC Controller status.

    Non-standardised DP type (in accordance with KNX AN 097/07 rev 3).

    Help needed:
    The values of this type were retrieved by reverse engineering. Any
    notes on the correct implementation of this type are highly appreciated.
    """

    data_type = HVACOperationMode
    VALUE_MAP = {
        0x21: HVACOperationMode.COMFORT,
        0x22: HVACOperationMode.STANDBY,
        0x24: HVACOperationMode.NIGHT,
        0x28: HVACOperationMode.FROST_PROTECTION,
    }

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> HVACOperationMode:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        if raw[0] & 8 > 0:
            return HVACOperationMode.FROST_PROTECTION
        if raw[0] & 4 > 0:
            return HVACOperationMode.NIGHT
        if raw[0] & 2 > 0:
            return HVACOperationMode.STANDBY
        if raw[0] & 1 > 0:
            return HVACOperationMode.COMFORT
        raise ConversionError(f"Payload not supported for {cls.__name__}", raw=raw)
