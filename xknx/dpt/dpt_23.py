"""Implementation of KNX 2 bit enumeration (N2) data point types (DPT 23.xxx)."""

from __future__ import annotations

from .dpt import DPTEnum, DPTEnumData
from .payload import DPTBinary


class OnOffAction(DPTEnumData):
    """
    Enum for the KNX on/off actions.

    DPT 23.001 DPT_OnOffAction - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.23
    """

    OFF = 0
    ON = 1
    OFF_ON = 2
    ON_OFF = 3


class DPTOnOffAction(DPTEnum[OnOffAction]):
    """
    Abstraction for DPT 23.001 DPT_OnOffAction.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.23
    """

    payload_type = DPTBinary
    payload_length = 2
    dpt_main_number = 23
    dpt_sub_number = 1
    value_type = "on_off_action"
    data_type = OnOffAction

    @classmethod
    def _to_knx(cls, value: OnOffAction) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class AlarmReaction(DPTEnumData):
    """
    Enum for the KNX alarm reactions; value 3 is reserved.

    DPT 23.002 DPT_Alarm_Reaction - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.23
    """

    NO_ALARM = 0
    ALARM_POSITION_UP = 1
    ALARM_POSITION_DOWN = 2


class DPTAlarmReaction(DPTEnum[AlarmReaction]):
    """
    Abstraction for DPT 23.002 DPT_Alarm_Reaction.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.23
    """

    payload_type = DPTBinary
    payload_length = 2
    dpt_main_number = 23
    dpt_sub_number = 2
    value_type = "alarm_reaction"
    data_type = AlarmReaction

    @classmethod
    def _to_knx(cls, value: AlarmReaction) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class UpDownAction(DPTEnumData):
    """
    Enum for the KNX up/down actions.

    DPT 23.003 DPT_UpDown_Action - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.23
    """

    UP = 0
    DOWN = 1
    UP_DOWN = 2
    DOWN_UP = 3


class DPTUpDownAction(DPTEnum[UpDownAction]):
    """
    Abstraction for DPT 23.003 DPT_UpDown_Action.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.23
    """

    payload_type = DPTBinary
    payload_length = 2
    dpt_main_number = 23
    dpt_sub_number = 3
    value_type = "up_down_action"
    data_type = UpDownAction

    @classmethod
    def _to_knx(cls, value: UpDownAction) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)


class HVACPBAction(DPTEnumData):
    """
    Enum for the KNX HVAC push button actions.

    DPT 23.102 DPT_HVAC_PB_Action - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.6
    """

    COMFORT_ECONOMY = 0
    COMFORT_NOTHING = 1
    ECONOMY_NOTHING = 2
    BUILDING_PROTECTION_AUTO = 3


class DPTHVACPBAction(DPTEnum[HVACPBAction]):
    """
    Abstraction for DPT 23.102 DPT_HVAC_PB_Action.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.6
    """

    payload_type = DPTBinary
    payload_length = 2
    dpt_main_number = 23
    dpt_sub_number = 102
    value_type = "hvac_pb_action"
    data_type = HVACPBAction

    @classmethod
    def _to_knx(cls, value: HVACPBAction) -> DPTBinary:
        """Return the raw KNX value for an Enum member."""
        return DPTBinary(value.value)
