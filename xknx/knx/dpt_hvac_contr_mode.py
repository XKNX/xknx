"""Implementation of different KNX DPT HVAC Operation modes."""

from xknx.exceptions import ConversionError, CouldNotParseKNXIP

from .dpt import DPTBase
from .dpt_hvac_mode import HVACOperationMode


class DPTHVACContrMode(DPTBase):
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
        20: HVACOperationMode.NODEM}

    SUPPORTED_MODES_INV = dict((reversed(item) for item in SUPPORTED_MODES.items()))

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data."""
        cls.test_bytesarray(raw, 1)
        if raw[0] in DPTHVACContrMode.SUPPORTED_MODES:
            return DPTHVACContrMode.SUPPORTED_MODES[raw[0]]
        raise CouldNotParseKNXIP("Could not parse DPTHVACContrMode")

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        if value in DPTHVACContrMode.SUPPORTED_MODES_INV:
            return (DPTHVACContrMode.SUPPORTED_MODES_INV[value],)
        raise ConversionError("Could not parse DPTHVACContrMode", value=value)
