"""Implementation of Basic KNX DPT B1U3 Values (DPT 3.007/3.008).

There are two separate dimming modes sharing the same DPT class:

 * Stepwise dimming
   The full brightness range is divided into 2^(stepcode-1) intervals.
   The value is always rounded to full interval boundary, i.e. 30% +25% = 50%, 50% +25% = 75%, 30% -25% = 25%

 * Start-stop dimming
   Dimming is started with -/+100% (0x1/0x9) and keeps dimming until a STOP diagram (0x0/0x8) is received.

As the same payload in these cases in interpreted completely different it is reasonable to make separate DPT classes.
"""
from enum import Enum
from typing import Tuple

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPTControlStepCode(DPTBase):
    """Abstraction for KNX B1U3 values (DPT 3.007/3.008)."""

    # APCI (application layer control information)
    APCI_CONTROLMASK = 0x08
    APCI_STEPCODEMASK = 0x07
    APCI_MAX_VALUE = APCI_CONTROLMASK | APCI_STEPCODEMASK

    value_type = "control_stepcode"
    unit = ""
    payload_length = 1

    @classmethod
    def _encode(cls, control: bool, step_code: int):
        """Encode control-bit with step-code."""
        value = 1 if control > 0 else 0
        value = (value << 3) | (step_code & cls.APCI_STEPCODEMASK)
        return value

    @classmethod
    def _decode(cls, value) -> Tuple[bool, int]:
        """Decode value into control-bit and step-code."""
        control = 1 if (value & cls.APCI_CONTROLMASK) != 0 else 0
        step_code = value & cls.APCI_STEPCODEMASK
        return control, step_code

    @classmethod
    def _test_boundaries(cls, raw):
        """Test if raw KNX data is within defined range for this object."""
        if isinstance(raw, int):
            return 0 <= raw <= cls.APCI_MAX_VALUE
        return False

    @classmethod
    def _test_values(cls, control: bool, step_code: int):
        """Test if input values are valid."""
        if isinstance(control, int) and isinstance(step_code, int):
            if control in (0, 1) and 0 <= step_code <= cls.APCI_STEPCODEMASK:
                return True
        return False

    @classmethod
    def to_knx(cls, value, invert: bool = False):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, dict):
            raise ConversionError(
                "Cant serialize %s; invalid value type" % cls.__name__, value=value
            )

        try:
            control = value["control"]
            step_code = value["step_code"]
        except KeyError:
            raise ConversionError(
                "Cant serialize %s; invalid keys" % cls.__name__, value=value
            )

        if not cls._test_values(control, step_code):
            raise ConversionError(
                "Cant serialize %s; invalid values" % cls.__name__, value=value
            )

        if invert:
            control = 0 if control > 0 else 1

        return cls._encode(control, step_code)

    @classmethod
    def from_knx(cls, raw, invert: bool = False):
        """Parse/deserialize from KNX/IP raw data."""
        if not cls._test_boundaries(raw):
            raise ConversionError("Cant parse %s" % cls.__name__, raw=raw)

        control, step_code = cls._decode(raw)

        if invert:
            control = 0 if control > 0 else 1

        return {"control": control, "step_code": step_code}


class DPTControlStepwise(DPTControlStepCode):
    """Abstraction for KNX DPT 3.xxx in stepwise mode with conversion to an incement value."""

    dpt_main_number = 3
    dpt_sub_number = None
    value_type = "stepwise"
    unit = "%"

    @staticmethod
    def _from_increment(value):
        """Calculate control bit and stepcode as defined in the KNX standard section 3.3.1 from an increment value."""
        # control bit in KNX standard
        #   0: - = decrease/move up
        #   1: + = increase/move down
        control = 0 if value <= 0 else 1

        stepcode = (
            0  # special case = break indication (e.g. stop dimming/moving blinds)
        )
        if abs(value) >= 100:
            stepcode = 1
        elif abs(value) >= 50:
            stepcode = 2
        elif abs(value) >= 25:
            stepcode = 3
        elif abs(value) >= 12:
            stepcode = 4
        elif abs(value) >= 6:
            stepcode = 5
        elif abs(value) >= 3:
            stepcode = 6
        elif abs(value) >= 1:
            stepcode = 7

        return {"control": control, "step_code": stepcode}

    @staticmethod
    def _to_increment(value):
        """Calculate the increment value from the stepcode and control bit as defined in the KNX standard section 3.3.1."""
        # calculated using floor(100/2^((value&0x07)-1))
        inc = [0, 100, 50, 25, 12, 6, 3, 1][value["step_code"] & 0x07]
        return inc if value["control"] == 1 else -inc

    @classmethod
    def to_knx(cls, value, invert: bool = False):
        """Serialize to KNX/IP raw data."""
        if not isinstance(value, int):
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

        return super().to_knx(cls._from_increment(value), invert)

    @classmethod
    def from_knx(cls, raw, invert: bool = False):
        """Parse/deserialize from KNX/IP raw data."""
        return cls._to_increment(super().from_knx(raw, invert))


class DPTControlStepwiseDimming(DPTControlStepwise):
    """Abstraction for KNX DPT 3.007 / DPT_Control_Dimming in stepwise mode."""

    dpt_main_number = 3
    dpt_sub_number = 7
    value_type = "stepwise_dimming"


class DPTControlStepwiseBlinds(DPTControlStepwise):
    """Abstraction for KNX DPT 3.008 / DPT_Control_Blinds in stepwise mode."""

    dpt_main_number = 3
    dpt_sub_number = 8
    value_type = "stepwise_blinds"


class TitleEnum(Enum):
    """Enum with a descriptive string representation.

    Ensures values are rendered nicely, e.g. in home assistant.
    """

    def __str__(self) -> str:
        """Return string representation."""
        # pylint: disable=no-member
        return self.name.title()


class DPTControlStartStop(DPTControlStepCode):
    """Abstraction for KNX DPT 3.xxx in start/stop mode."""

    value_type = "startstop"
    unit = ""

    class Direction(TitleEnum):
        """Enum for indicating the direction."""

        DECREASE = 0
        INCREASE = 1
        STOP = 2

    @classmethod
    def to_knx(cls, value, invert: bool = False):
        """Convert value to payload."""
        control = 0
        step_code = 0
        if value == cls.Direction(1):  # INCREASE/DOWN
            control = 1
            step_code = 1
        elif value == cls.Direction(0):  # DECREASE/UP
            control = 0
            step_code = 1
        elif value == cls.Direction(2):  # STOP
            control = 0
            step_code = 0
        else:
            raise ConversionError("Cant serialize %s" % cls.__name__, value=value)

        values = {"control": control, "step_code": step_code}
        return super().to_knx(values, invert)

    @classmethod
    def from_knx(cls, raw, invert: bool = False):
        """Convert current payload to value."""
        values = super().from_knx(raw, invert)
        if values["step_code"] == 0:
            return cls.Direction(2)  # STOP
        if values["control"] == 0:
            return cls.Direction(0)  # DECREASE/UP
        return cls.Direction(1)  # INCREASE/DOWN


class DPTControlStartStopDimming(DPTControlStartStop):
    """Abstraction for KNX DPT 3.007 / DPT_Control_Dimming in start/stop mode."""

    value_type = "startstop_dimming"

    # redefining Direction enum ensures proper typing, e.g.
    # DPTControlStartStop.Direction.INCREASE != DPTControlStartStopDimming.Direction.INCREASE
    class Direction(TitleEnum):
        """Enum for indicating the direction."""

        DECREASE = 0
        INCREASE = 1
        STOP = 2


class DPTControlStartStopBlinds(DPTControlStartStop):
    """Abstraction for KNX DPT 3.008 / DPT_Control_Blinds in start/stop mode."""

    value_type = "startstop_blinds"

    class Direction(TitleEnum):
        """Enum for indicating the direction."""

        UP = 0
        DOWN = 1
        STOP = 2
