"""Unit test for the KNX enumeration data point types DPT 20.xxx (N8) and 23.xxx (N2)."""

import pytest

from xknx.dpt import (
    DPTActuatorConnectType,
    DPTADAType,
    DPTAddInfoTypes,
    DPTAlarmClassType,
    DPTAlarmReaction,
    DPTApplicationArea,
    DPTArray,
    DPTBackupMode,
    DPTBase,
    DPTBeaufortWindForceScale,
    DPTBehaviourBusPowerUpDown,
    DPTBehaviourLockUnlock,
    DPTBinary,
    DPTBlindsControlMode,
    DPTBlinkingMode,
    DPTBuildingMode,
    DPTBurnerType,
    DPTCloudCover,
    DPTCommMode,
    DPTConverterControl,
    DPTConverterDataRequest,
    DPTConverterTestControl,
    DPTDALIFadeTime,
    DPTDamperMode,
    DPTDHWMode,
    DPTDimmPBModel,
    DPTEnum,
    DPTErrorClassHVAC,
    DPTFanMode,
    DPTFuelType,
    DPTHeaterMode,
    DPTHumDehumMode,
    DPTHVACEmergMode,
    DPTHVACPBAction,
    DPTLightApplicationMode,
    DPTLightControlMode,
    DPTLoadPriority,
    DPTLoadTypeDetected,
    DPTLoadTypeSet,
    DPTMasterSlaveMode,
    DPTMeteringDeviceType,
    DPTOccMode,
    DPTOnOffAction,
    DPTPBAction,
    DPTPowerReturnMode,
    DPTPriority,
    DPTPSUMode,
    DPTRFFilterSelect,
    DPTRFModeSelect,
    DPTSABBehaviourLockUnlock,
    DPTSABExceptBehaviour,
    DPTSCLOMode,
    DPTSensorSelect,
    DPTSSSBMode,
    DPTStartSynchronization,
    DPTStatusRoomSetp,
    DPTSwitchOnMode,
    DPTSwitchPBModel,
    DPTTimeDelay,
    DPTUpDownAction,
    DPTValveMode,
)
from xknx.dpt.dpt_20 import (
    CloudCover,
    CommMode,
    DamperMode,
    LoadTypeDetected,
    MeteringDeviceType,
    Priority,
)
from xknx.dpt.dpt_23 import AlarmReaction, HVACPBAction
from xknx.exceptions import ConversionError, CouldNotParseTelegram

N8_TYPES: list[type[DPTEnum]] = [
    DPTSCLOMode,
    DPTBuildingMode,
    DPTOccMode,
    DPTPriority,
    DPTLightApplicationMode,
    DPTApplicationArea,
    DPTAlarmClassType,
    DPTPSUMode,
    DPTErrorClassHVAC,
    DPTTimeDelay,
    DPTBeaufortWindForceScale,
    DPTSensorSelect,
    DPTActuatorConnectType,
    DPTCloudCover,
    DPTPowerReturnMode,
    DPTFuelType,
    DPTBurnerType,
    DPTDHWMode,
    DPTLoadPriority,
    DPTHVACEmergMode,
    DPTValveMode,
    DPTDamperMode,
    DPTHeaterMode,
    DPTFanMode,
    DPTMasterSlaveMode,
    DPTStatusRoomSetp,
    DPTMeteringDeviceType,
    DPTHumDehumMode,
    DPTADAType,
    DPTBackupMode,
    DPTStartSynchronization,
    DPTBehaviourLockUnlock,
    DPTBehaviourBusPowerUpDown,
    DPTDALIFadeTime,
    DPTBlinkingMode,
    DPTLightControlMode,
    DPTSwitchPBModel,
    DPTPBAction,
    DPTDimmPBModel,
    DPTSwitchOnMode,
    DPTLoadTypeSet,
    DPTLoadTypeDetected,
    DPTConverterTestControl,
    DPTConverterControl,
    DPTConverterDataRequest,
    DPTSABExceptBehaviour,
    DPTSABBehaviourLockUnlock,
    DPTSSSBMode,
    DPTBlindsControlMode,
    DPTCommMode,
    DPTAddInfoTypes,
    DPTRFModeSelect,
    DPTRFFilterSelect,
]
N2_TYPES: list[type[DPTEnum]] = [
    DPTOnOffAction,
    DPTAlarmReaction,
    DPTUpDownAction,
    DPTHVACPBAction,
]


def _payload(dpt: type[DPTEnum], raw: int) -> DPTArray | DPTBinary:
    return DPTBinary(raw) if dpt in N2_TYPES else DPTArray(raw)


@pytest.mark.parametrize("dpt", N8_TYPES + N2_TYPES)
def test_every_member_round_trips(dpt: type[DPTEnum]) -> None:
    """Test each member to and from KNX, also given by name and by value."""
    for member in dpt.data_type:
        payload = _payload(dpt, member.value)
        assert dpt.to_knx(member) == payload
        assert dpt.to_knx(member.name.lower()) == payload
        assert dpt.to_knx(member.value) == payload
        assert dpt.from_knx(payload) is member
    assert dpt.get_valid_values() == list(dpt.data_type)


@pytest.mark.parametrize("dpt", N8_TYPES + N2_TYPES)
def test_reserved_values_are_refused(dpt: type[DPTEnum]) -> None:
    """Test that the values without a member (reserved) raise ConversionError."""
    values = {member.value for member in dpt.data_type}
    for raw in range(4 if dpt in N2_TYPES else 256):
        if raw in values:
            continue
        with pytest.raises(ConversionError):
            dpt.from_knx(_payload(dpt, raw))
        with pytest.raises(ConversionError):
            dpt.to_knx(raw)
    with pytest.raises(ConversionError):
        dpt.to_knx("invalid")


@pytest.mark.parametrize("dpt", N8_TYPES)
def test_n8_payload_type_and_length(dpt: type[DPTEnum]) -> None:
    """Test that an N8 type only takes a 1 octet DPTArray."""
    with pytest.raises(CouldNotParseTelegram):
        dpt.from_knx(DPTArray((0, 0)))
    with pytest.raises(CouldNotParseTelegram):
        dpt.from_knx(DPTBinary(0))


@pytest.mark.parametrize("dpt", N2_TYPES)
def test_n2_payload_type_and_length(dpt: type[DPTEnum]) -> None:
    """Test that an N2 type only takes a 2 bit DPTBinary."""
    with pytest.raises(CouldNotParseTelegram):
        dpt.from_knx(DPTBinary(4))
    with pytest.raises(CouldNotParseTelegram):
        dpt.from_knx(DPTArray(0))


@pytest.mark.parametrize("dpt", N8_TYPES + N2_TYPES)
def test_lookup(dpt: type[DPTEnum]) -> None:
    """Test that the type is found by its value type and its number."""
    assert DPTBase.parse_transcoder(dpt.value_type) is dpt
    assert (
        DPTBase.transcoder_by_dpt(
            dpt_main=dpt.dpt_main_number, dpt_sub=dpt.dpt_sub_number
        )
        is dpt
    )
    assert dpt.unit is None


@pytest.mark.parametrize(
    ("dpt", "raw", "value"),
    [
        # KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21: 3 is 'void'
        (DPTPriority, 3, Priority.VOID),
        # §3.21: values 6 and 7 have no English name
        (DPTCloudCover, 6, CloudCover.MOSTLY_CLOUDY),
        (DPTCloudCover, 7, CloudCover.NEARLY_OVERCAST),
        (DPTCloudCover, 9, CloudCover.SKY_OBSTRUCTED_FROM_VIEW),
        # §4.3: 3 is discharge air, 4 extract air
        (DPTDamperMode, 3, DamperMode.DISCHARGE_AIR),
        (DPTDamperMode, 4, DamperMode.EXTRACT_AIR),
        (DPTMeteringDeviceType, 0xFF, MeteringDeviceType.VOID),
        (DPTLoadTypeDetected, 3, LoadTypeDetected.DETECTION_NOT_POSSIBLE),
        # KNX v01.04.02 - External Message Interface 03.06.03 - §4.2.2.4.2 Table 17
        (DPTCommMode, 0x06, CommMode.CEMI_TRANSPORT_LAYER),
        (DPTCommMode, 0xFF, CommMode.NO_LAYER),
        (DPTAlarmReaction, 2, AlarmReaction.ALARM_POSITION_DOWN),
        (DPTHVACPBAction, 3, HVACPBAction.BUILDING_PROTECTION_AUTO),
    ],
)
def test_values_from_the_standard(dpt: type[DPTEnum], raw: int, value: object) -> None:
    """Test values that the standard defines in a particular way."""
    assert dpt.from_knx(_payload(dpt, raw)) is value
    assert dpt.to_knx(value) == _payload(dpt, raw)
