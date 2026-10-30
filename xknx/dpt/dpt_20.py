"""Implementation of different KNX DPT HVAC Operation modes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .dpt import DPTComplex, DPTComplexData, DPTEnum, DPTEnumData
from .dpt_1 import HeatCool
from .payload import DPTArray, DPTBinary


class SCLOMode(DPTEnumData):
    """
    Enum for the KNX SCLO (sensor/controller/local operation) modes.

    DPT 20.001 DPT_SCLOMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    AUTONOMOUS = 0
    SLAVE = 1
    MASTER = 2


class DPTSCLOMode(DPTEnum[SCLOMode]):
    """
    Abstraction for DPT 20.001 DPT_SCLOMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 1
    value_type = "sclo_mode"
    data_type = SCLOMode

    @classmethod
    def _to_knx(cls, value: SCLOMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BuildingMode(DPTEnumData):
    """
    Enum for the KNX building modes.

    DPT 20.002 DPT_BuildingMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    BUILDING_IN_USE = 0
    BUILDING_NOT_USED = 1
    BUILDING_PROTECTION = 2


class DPTBuildingMode(DPTEnum[BuildingMode]):
    """
    Abstraction for DPT 20.002 DPT_BuildingMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 2
    value_type = "building_mode"
    data_type = BuildingMode

    @classmethod
    def _to_knx(cls, value: BuildingMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class OccupancyMode(DPTEnumData):
    """
    Enum for the KNX occupancy modes.

    DPT 20.003 DPT_OccMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    OCCUPIED = 0
    STANDBY = 1
    NOT_OCCUPIED = 2


class DPTOccMode(DPTEnum[OccupancyMode]):
    """
    Abstraction for DPT 20.003 DPT_OccMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 3
    value_type = "occupancy_mode"
    data_type = OccupancyMode

    @classmethod
    def _to_knx(cls, value: OccupancyMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class Priority(DPTEnumData):
    """
    Enum for the KNX priorities; 0 is the highest priority, 3 'void' is no priority.

    DPT 20.004 DPT_Priority - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21.
    DPT 219.001 DPT_AlarmInfo represents 'void' as None instead.
    """

    HIGH = 0
    MEDIUM = 1
    LOW = 2
    VOID = 3


class DPTPriority(DPTEnum[Priority]):
    """
    Abstraction for DPT 20.004 DPT_Priority.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 4
    value_type = "priority"
    data_type = Priority

    @classmethod
    def _to_knx(cls, value: Priority) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class LightApplicationMode(DPTEnumData):
    """
    Enum for the KNX light application modes.

    DPT 20.005 DPT_LightApplicationMode - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §3.21

    Values 17 to 255 are manufacturer specific, the others reserved.
    """

    NORMAL = 0
    PRESENCE_SIMULATION = 1
    NIGHT_ROUND = 2


class DPTLightApplicationMode(DPTEnum[LightApplicationMode]):
    """
    Abstraction for DPT 20.005 DPT_LightApplicationMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 5
    value_type = "light_application_mode"
    data_type = LightApplicationMode

    @classmethod
    def _to_knx(cls, value: LightApplicationMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ApplicationArea(DPTEnumData):
    """
    Enum for the KNX application areas; other values are reserved.

    DPT 20.006 DPT_ApplicationArea - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §3.21. The codes correspond to the numbering of the parts in Volume 7 of
    the KNX Standard.
    """

    NO_FAULT = 0
    SYSTEM_AND_FUNCTIONS_OF_COMMON_INTEREST = 1
    HVAC_GENERAL_FBS = 10
    HVAC_HOT_WATER_HEATING = 11
    HVAC_DIRECT_ELECTRICAL_HEATING = 12
    HVAC_TERMINAL_UNITS = 13
    HVAC_VAC = 14
    LIGHTING = 20
    SECURITY = 30
    LOAD_MANAGEMENT = 40
    SHUTTERS_AND_BLINDS = 50


class DPTApplicationArea(DPTEnum[ApplicationArea]):
    """
    Abstraction for DPT 20.006 DPT_ApplicationArea.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 6
    value_type = "application_area"
    data_type = ApplicationArea

    @classmethod
    def _to_knx(cls, value: ApplicationArea) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class AlarmClassType(DPTEnumData):
    """
    Enum for the KNX alarm classes; value 0 is reserved.

    DPT 20.007 DPT_AlarmClassType - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    SIMPLE_ALARM = 1
    BASIC_ALARM = 2
    EXTENDED_ALARM = 3


class DPTAlarmClassType(DPTEnum[AlarmClassType]):
    """
    Abstraction for DPT 20.007 DPT_AlarmClassType.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 7
    value_type = "alarm_class_type"
    data_type = AlarmClassType

    @classmethod
    def _to_knx(cls, value: AlarmClassType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class PSUMode(DPTEnumData):
    """
    Enum for the KNX power supply unit (PSU/DPSU) modes.

    DPT 20.008 DPT_PSUMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    DISABLED = 0
    ENABLED = 1
    AUTO = 2


class DPTPSUMode(DPTEnum[PSUMode]):
    """
    Abstraction for DPT 20.008 DPT_PSUMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 8
    value_type = "psu_mode"
    data_type = PSUMode

    @classmethod
    def _to_knx(cls, value: PSUMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ErrorClassSystem(DPTEnumData):
    """
    Enum for the KNX system error classes.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21: values 19 to 255 are
    reserved and shall not be used.
    """

    NO_FAULT = 0
    GENERAL_DEVICE_FAULT = 1
    COMMUNICATION_FAULT = 2
    CONFIGURATION_FAULT = 3
    HARDWARE_FAULT = 4
    SOFTWARE_FAULT = 5
    INSUFFICIENT_NON_VOLATILE_MEMORY = 6
    INSUFFICIENT_VOLATILE_MEMORY = 7
    MEMORY_ALLOCATION_COMMAND_WITH_SIZE_0_RECEIVED = 8
    CRC_ERROR = 9
    WATCHDOG_RESET_DETECTED = 10
    INVALID_OPCODE_DETECTED = 11
    GENERAL_PROTECTION_FAULT = 12
    MAXIMAL_TABLE_LENGTH_EXCEEDED = 13
    UNDEFINED_LOAD_COMMAND_RECEIVED = 14
    GROUP_ADDRESS_TABLE_IS_NOT_SORTED = 15
    INVALID_CONNECTION_NUMBER = 16
    INVALID_GROUP_OBJECT_NUMBER = 17
    GROUP_OBJECT_TYPE_EXCEEDS_MAX_APDU_LENGTH = 18


class ErrorClassHVAC(DPTEnumData):
    """
    Enum for the KNX HVAC error classes; values 5 to 255 are reserved.

    DPT 20.012 DPT_ErrorClass_HVAC - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §3.21
    """

    NO_FAULT = 0
    SENSOR_FAULT = 1
    PROCESS_FAULT_CONTROLLER_FAULT = 2
    ACTUATOR_FAULT = 3
    OTHER_FAULT = 4


class DPTErrorClassHVAC(DPTEnum[ErrorClassHVAC]):
    """
    Abstraction for DPT 20.012 DPT_ErrorClass_HVAC.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 12
    value_type = "error_class_hvac"
    data_type = ErrorClassHVAC

    @classmethod
    def _to_knx(cls, value: ErrorClassHVAC) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class TimeDelay(DPTEnumData):
    """
    Enum for the KNX time delays.

    DPT 20.013 DPT_Time_Delay - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    NOT_ACTIVE = 0
    DELAY_1_S = 1
    DELAY_2_S = 2
    DELAY_3_S = 3
    DELAY_5_S = 4
    DELAY_10_S = 5
    DELAY_15_S = 6
    DELAY_20_S = 7
    DELAY_30_S = 8
    DELAY_45_S = 9
    DELAY_1_MIN = 10
    DELAY_1_25_MIN = 11
    DELAY_1_5_MIN = 12
    DELAY_2_MIN = 13
    DELAY_2_5_MIN = 14
    DELAY_3_MIN = 15
    DELAY_5_MIN = 16
    DELAY_15_MIN = 17
    DELAY_20_MIN = 18
    DELAY_30_MIN = 19
    DELAY_1_H = 20
    DELAY_2_H = 21
    DELAY_3_H = 22
    DELAY_5_H = 23
    DELAY_12_H = 24
    DELAY_24_H = 25


class DPTTimeDelay(DPTEnum[TimeDelay]):
    """
    Abstraction for DPT 20.013 DPT_Time_Delay.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 13
    value_type = "time_delay"
    data_type = TimeDelay

    @classmethod
    def _to_knx(cls, value: TimeDelay) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BeaufortWindForceScale(DPTEnumData):
    """
    Enum for the Beaufort wind force scale.

    DPT 20.014 DPT_Beaufort_Wind_Force_Scale - KNX v02.02.01 - Datapoint Types 03.07.02
    - §3.21
    """

    CALM = 0
    LIGHT_AIR = 1
    LIGHT_BREEZE = 2
    GENTLE_BREEZE = 3
    MODERATE_BREEZE = 4
    FRESH_BREEZE = 5
    STRONG_BREEZE = 6
    NEAR_GALE = 7
    FRESH_GALE = 8
    STRONG_GALE = 9
    WHOLE_GALE = 10
    VIOLENT_STORM = 11
    HURRICANE = 12


class DPTBeaufortWindForceScale(DPTEnum[BeaufortWindForceScale]):
    """
    Abstraction for DPT 20.014 DPT_Beaufort_Wind_Force_Scale.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 14
    value_type = "beaufort_wind_force_scale"
    data_type = BeaufortWindForceScale

    @classmethod
    def _to_knx(cls, value: BeaufortWindForceScale) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class SensorSelect(DPTEnumData):
    """
    Enum for the KNX sensor input modes.

    DPT 20.017 DPT_SensorSelect - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    INACTIVE = 0
    DIGITAL_INPUT_NOT_INVERTED = 1
    DIGITAL_INPUT_INVERTED = 2
    ANALOG_INPUT = 3
    TEMPERATURE_SENSOR_INPUT = 4


class DPTSensorSelect(DPTEnum[SensorSelect]):
    """
    Abstraction for DPT 20.017 DPT_SensorSelect.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 17
    value_type = "sensor_select"
    data_type = SensorSelect

    @classmethod
    def _to_knx(cls, value: SensorSelect) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ActuatorConnectType(DPTEnumData):
    """
    Enum for the KNX actuator connection types; value 0 is reserved.

    DPT 20.020 DPT_ActuatorConnectType - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §3.21
    """

    SENSOR_CONNECTION = 1
    CONTROLLER_CONNECTION = 2


class DPTActuatorConnectType(DPTEnum[ActuatorConnectType]):
    """
    Abstraction for DPT 20.020 DPT_ActuatorConnectType.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 20
    value_type = "actuator_connect_type"
    data_type = ActuatorConnectType

    @classmethod
    def _to_knx(cls, value: ActuatorConnectType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class CloudCover(DPTEnumData):
    """
    Enum for the KNX cloud cover in oktas, plus 9 for a sky obstructed from view.

    DPT 20.021 DPT_Cloud_Cover - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21

    The values 6 and 7 have no English name in the standard ("Not all okta values
    have a name"); their names follow the German ones, "stark bewölkt" and "fast
    bedeckt".
    """

    CLOUDLESS = 0
    SUNNY = 1
    SUNSHINY = 2
    LIGHTLY_CLOUDY = 3
    SCATTERED_CLOUDS = 4
    CLOUDY = 5
    MOSTLY_CLOUDY = 6
    NEARLY_OVERCAST = 7
    OVERCAST = 8
    SKY_OBSTRUCTED_FROM_VIEW = 9


class DPTCloudCover(DPTEnum[CloudCover]):
    """
    Abstraction for DPT 20.021 DPT_Cloud_Cover.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 21
    value_type = "cloud_cover"
    data_type = CloudCover

    @classmethod
    def _to_knx(cls, value: CloudCover) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class PowerReturnMode(DPTEnumData):
    """
    Enum for the KNX power return modes (sending after bus power return).

    DPT 20.022 DPT_PowerReturnMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    DO_NOT_SEND = 0
    SEND_ALWAYS = 1
    SEND_IF_VALUE_CHANGED = 2


class DPTPowerReturnMode(DPTEnum[PowerReturnMode]):
    """
    Abstraction for DPT 20.022 DPT_PowerReturnMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.21
    """

    dpt_main_number = 20
    dpt_sub_number = 22
    value_type = "power_return_mode"
    data_type = PowerReturnMode

    @classmethod
    def _to_knx(cls, value: PowerReturnMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class FuelType(DPTEnumData):
    """
    Enum for the KNX fuel types.

    DPT 20.100 DPT_FuelType - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    AUTO = 0
    OIL = 1
    GAS = 2
    SOLID_STATE_FUEL = 3


class DPTFuelType(DPTEnum[FuelType]):
    """
    Abstraction for DPT 20.100 DPT_FuelType.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 100
    value_type = "fuel_type"
    data_type = FuelType

    @classmethod
    def _to_knx(cls, value: FuelType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BurnerType(DPTEnumData):
    """
    Enum for the KNX burner types; value 0 is reserved.

    DPT 20.101 DPT_BurnerType - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    ONE_STAGE = 1
    TWO_STAGE = 2
    MODULATING = 3


class DPTBurnerType(DPTEnum[BurnerType]):
    """
    Abstraction for DPT 20.101 DPT_BurnerType.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 101
    value_type = "burner_type"
    data_type = BurnerType

    @classmethod
    def _to_knx(cls, value: BurnerType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HVACOperationMode(DPTEnumData):
    """Enum for the different KNX HVAC operation modes."""

    AUTO = 0
    COMFORT = 1
    STANDBY = 2
    ECONOMY = 3
    BUILDING_PROTECTION = 4


class DPTHVACMode(DPTEnum[HVACOperationMode]):
    """
    Abstraction for KNX HVAC mode.

    DPT 20.102
    """

    dpt_main_number = 20
    dpt_sub_number = 102
    value_type = "hvac_mode"
    data_type = HVACOperationMode

    @classmethod
    def _to_knx(cls, value: HVACOperationMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class DHWMode(DPTEnumData):
    """
    Enum for the KNX domestic hot water modes.

    DPT 20.103 DPT_DHWMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    AUTO = 0
    LEGIO_PROTECT = 1
    NORMAL = 2
    REDUCED = 3
    OFF_FROST_PROTECT = 4


class DPTDHWMode(DPTEnum[DHWMode]):
    """
    Abstraction for DPT 20.103 DPT_DHWMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 103
    value_type = "dhw_mode"
    data_type = DHWMode

    @classmethod
    def _to_knx(cls, value: DHWMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class LoadPriority(DPTEnumData):
    """
    Enum for the KNX load priorities.

    DPT 20.104 DPT_LoadPriority - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    NONE = 0
    SHIFT_LOAD_PRIORITY = 1
    ABSOLUTE_LOAD_PRIORITY = 2


class DPTLoadPriority(DPTEnum[LoadPriority]):
    """
    Abstraction for DPT 20.104 DPT_LoadPriority.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 104
    value_type = "load_priority"
    data_type = LoadPriority

    @classmethod
    def _to_knx(cls, value: LoadPriority) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HVACControllerMode(DPTEnumData):
    """Enum for the different KNX HVAC controller modes."""

    AUTO = 0
    HEAT = 1
    MORNING_WARMUP = 2
    COOL = 3
    NIGHT_PURGE = 4
    PRECOOL = 5
    OFF = 6
    TEST = 7
    EMERGENCY_HEAT = 8
    FAN_ONLY = 9
    FREE_COOL = 10
    ICE = 11
    MAXIMUM_HEATING_MODE = 12
    ECONOMIC_HEAT_COOL_MODE = 13
    DEHUMIDIFICATION = 14
    CALIBRATION_MODE = 15
    EMERGENCY_COOL_MODE = 16
    EMERGENCY_STEAM_MODE = 17
    NODEM = 20


class DPTHVACContrMode(DPTEnum[HVACControllerMode]):
    """
    Abstraction for KNX HVAC controller mode.

    DPT 20.105
    """

    dpt_main_number = 20
    dpt_sub_number = 105
    value_type = "hvac_controller_mode"
    data_type = HVACControllerMode

    @classmethod
    def _to_knx(cls, value: HVACControllerMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HVACEmergencyMode(DPTEnumData):
    """
    Enum for the KNX HVAC emergency modes.

    DPT 20.106 DPT_HVACEmergMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    NORMAL = 0
    EMERGENCY_PRESSURE = 1
    EMERGENCY_DEPRESSURE = 2
    EMERGENCY_PURGE = 3
    EMERGENCY_SHUTDOWN = 4
    EMERGENCY_FIRE = 5


class DPTHVACEmergMode(DPTEnum[HVACEmergencyMode]):
    """
    Abstraction for DPT 20.106 DPT_HVACEmergMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 106
    value_type = "hvac_emergency_mode"
    data_type = HVACEmergencyMode

    @classmethod
    def _to_knx(cls, value: HVACEmergencyMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ChangeoverMode(DPTEnumData):
    """
    Enum for the KNX heating/cooling changeover modes.

    DPT 20.107 DPT_ChangeoverMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    AUTO = 0
    COOLING_ONLY = 1
    HEATING_ONLY = 2


class DPTChangeoverMode(DPTEnum[ChangeoverMode]):
    """
    Abstraction for KNX changeover mode (DPT 20.107 DPT_ChangeoverMode).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 107
    value_type = "changeover_mode"
    data_type = ChangeoverMode

    @classmethod
    def _to_knx(cls, value: ChangeoverMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ValveMode(DPTEnumData):
    """
    Enum for the KNX valve modes; value 0 is reserved.

    DPT 20.108 DPT_ValveMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    HEAT_STAGE_A = 1
    HEAT_STAGE_B = 2
    COOL_STAGE_A = 3
    COOL_STAGE_B = 4
    HEAT_COOL = 5


class DPTValveMode(DPTEnum[ValveMode]):
    """
    Abstraction for DPT 20.108 DPT_ValveMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 108
    value_type = "valve_mode"
    data_type = ValveMode

    @classmethod
    def _to_knx(cls, value: ValveMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class DamperMode(DPTEnumData):
    """
    Enum for the KNX damper modes; value 0 is reserved.

    DPT 20.109 DPT_DamperMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    FRESH_AIR = 1
    SUPPLY_AIR = 2
    DISCHARGE_AIR = 3
    EXTRACT_AIR = 4


class DPTDamperMode(DPTEnum[DamperMode]):
    """
    Abstraction for DPT 20.109 DPT_DamperMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 109
    value_type = "damper_mode"
    data_type = DamperMode

    @classmethod
    def _to_knx(cls, value: DamperMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HeaterMode(DPTEnumData):
    """
    Enum for the KNX heater modes; value 0 is reserved.

    DPT 20.110 DPT_HeaterMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    HEAT_STAGE_A_ON_OFF = 1
    HEAT_STAGE_A_PROPORTIONAL = 2
    HEAT_STAGE_B_PROPORTIONAL = 3


class DPTHeaterMode(DPTEnum[HeaterMode]):
    """
    Abstraction for DPT 20.110 DPT_HeaterMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 110
    value_type = "heater_mode"
    data_type = HeaterMode

    @classmethod
    def _to_knx(cls, value: HeaterMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class FanMode(DPTEnumData):
    """
    Enum for the KNX fan modes.

    DPT 20.111 DPT_FanMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    NOT_RUNNING = 0
    PERMANENTLY_RUNNING = 1
    RUNNING_IN_INTERVALS = 2


class DPTFanMode(DPTEnum[FanMode]):
    """
    Abstraction for DPT 20.111 DPT_FanMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 111
    value_type = "fan_mode"
    data_type = FanMode

    @classmethod
    def _to_knx(cls, value: FanMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class MasterSlaveMode(DPTEnumData):
    """
    Enum for the KNX master/slave modes.

    DPT 20.112 DPT_MasterSlaveMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    AUTONOMOUS = 0
    MASTER = 1
    SLAVE = 2


class DPTMasterSlaveMode(DPTEnum[MasterSlaveMode]):
    """
    Abstraction for DPT 20.112 DPT_MasterSlaveMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 112
    value_type = "master_slave_mode"
    data_type = MasterSlaveMode

    @classmethod
    def _to_knx(cls, value: MasterSlaveMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class StatusRoomSetpoint(DPTEnumData):
    """
    Enum for the KNX room setpoint states.

    DPT 20.113 DPT_StatusRoomSetp - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    NORMAL_SETPOINT = 0
    ALTERNATIVE_SETPOINT = 1
    BUILDING_PROTECTION_SETPOINT = 2


class DPTStatusRoomSetp(DPTEnum[StatusRoomSetpoint]):
    """
    Abstraction for DPT 20.113 DPT_StatusRoomSetp.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 113
    value_type = "status_room_setpoint"
    data_type = StatusRoomSetpoint

    @classmethod
    def _to_knx(cls, value: StatusRoomSetpoint) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class MeteringDeviceType(DPTEnumData):
    """
    Enum for the KNX metering device types (measured media).

    DPT 20.114 DPT_Metering_DeviceType - KNX v02.02.01 - Datapoint Types
    03.07.02 - §4.3. The codes are those of the M-Bus device types (EN 13757-3)
    supported by KNX; the other M-Bus codes are reserved.
    """

    OTHER = 0x00
    OIL_METER = 0x01
    ELECTRICITY_METER = 0x02
    GAS_METER = 0x03
    HEAT_METER = 0x04
    STEAM_METER = 0x05
    WARM_WATER_METER = 0x06
    WATER_METER = 0x07
    HEAT_COST_ALLOCATOR = 0x08
    COOLING_LOAD_METER_OUTLET = 0x0A
    COOLING_LOAD_METER_INLET = 0x0B
    HEAT_INLET = 0x0C
    HEAT_AND_COOL = 0x0D
    BREAKER = 0x20
    VALVE = 0x21
    WASTE_WATER_METER = 0x28
    GARBAGE = 0x29
    VOID = 0xFF


class DPTMeteringDeviceType(DPTEnum[MeteringDeviceType]):
    """
    Abstraction for DPT 20.114 DPT_Metering_DeviceType.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 114
    value_type = "metering_device_type"
    data_type = MeteringDeviceType

    @classmethod
    def _to_knx(cls, value: MeteringDeviceType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class HumDehumMode(DPTEnumData):
    """
    Enum for the KNX humidification/dehumidification modes.

    DPT 20.115 DPT_HumDehumMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    INACTIVE = 0
    HUMIDIFICATION = 1
    DEHUMIDIFICATION = 2


class DPTHumDehumMode(DPTEnum[HumDehumMode]):
    """
    Abstraction for DPT 20.115 DPT_HumDehumMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 115
    value_type = "hum_dehum_mode"
    data_type = HumDehumMode

    @classmethod
    def _to_knx(cls, value: HumDehumMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class EnableHCStage(DPTEnumData):
    """
    Enum for enabling the heating/cooling stages A and B.

    DPT 20.116 DPT_EnableHCStage - KNX v01.03.01 - HVAC S-Mode FBs 07.19.20 - §9.6
    """

    DISABLED = 0
    STAGE_A = 1
    STAGE_B = 2
    BOTH_STAGES = 3


class DPTEnableHCStage(DPTEnum[EnableHCStage]):
    """
    Abstraction for KNX enable heating/cooling stage (DPT 20.116 DPT_EnableHCStage).

    KNX v01.03.01 - HVAC S-Mode FBs 07.19.20 - §9.6
    """

    dpt_main_number = 20
    dpt_sub_number = 116
    value_type = "enable_hc_stage"
    data_type = EnableHCStage

    @classmethod
    def _to_knx(cls, value: EnableHCStage) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ADAType(DPTEnumData):
    """
    Enum for the KNX air damper actuator types; value 0 is reserved.

    DPT 20.120 DPT_ADAType - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    AIR_DAMPER = 1
    VAV = 2


class DPTADAType(DPTEnum[ADAType]):
    """
    Abstraction for DPT 20.120 DPT_ADAType.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 120
    value_type = "ada_type"
    data_type = ADAType

    @classmethod
    def _to_knx(cls, value: ADAType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BackupMode(DPTEnumData):
    """
    Enum for the KNX backup modes.

    DPT 20.121 DPT_BackupMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    BACKUP_VALUE = 0
    KEEP_LAST_STATE = 1


class DPTBackupMode(DPTEnum[BackupMode]):
    """
    Abstraction for DPT 20.121 DPT_BackupMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 121
    value_type = "backup_mode"
    data_type = BackupMode

    @classmethod
    def _to_knx(cls, value: BackupMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class StartSynchronization(DPTEnumData):
    """
    Enum for the KNX start synchronization types.

    DPT 20.122 DPT_StartSynchronization - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §4.3
    """

    POSITION_UNCHANGED = 0
    SINGLE_CLOSE = 1
    SINGLE_OPEN = 2


class DPTStartSynchronization(DPTEnum[StartSynchronization]):
    """
    Abstraction for DPT 20.122 DPT_StartSynchronization.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.3
    """

    dpt_main_number = 20
    dpt_sub_number = 122
    value_type = "start_synchronization"
    data_type = StartSynchronization

    @classmethod
    def _to_knx(cls, value: StartSynchronization) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BehaviourLockUnlock(DPTEnumData):
    """
    Enum for the KNX behaviours on locking and unlocking.

    DPT 20.600 DPT_Behaviour_Lock_Unlock - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §6.3
    """

    OFF = 0
    ON = 1
    NO_CHANGE = 2
    ADDITIONAL_PARAMETER = 3
    MEMORY_FUNCTION_VALUE = 4
    UPDATED_VALUE = 5
    VALUE_BEFORE_LOCKING = 6


class DPTBehaviourLockUnlock(DPTEnum[BehaviourLockUnlock]):
    """
    Abstraction for DPT 20.600 DPT_Behaviour_Lock_Unlock.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 600
    value_type = "behaviour_lock_unlock"
    data_type = BehaviourLockUnlock

    @classmethod
    def _to_knx(cls, value: BehaviourLockUnlock) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BehaviourBusPowerUpDown(DPTEnumData):
    """
    Enum for the KNX behaviours on bus power up and down.

    DPT 20.601 DPT_Behaviour_Bus_Power_Up_Down - KNX v02.02.01 - Datapoint Types
    03.07.02 - §6.3
    """

    OFF = 0
    ON = 1
    NO_CHANGE = 2
    ADDITIONAL_PARAMETER = 3
    LAST_VALUE = 4


class DPTBehaviourBusPowerUpDown(DPTEnum[BehaviourBusPowerUpDown]):
    """
    Abstraction for DPT 20.601 DPT_Behaviour_Bus_Power_Up_Down.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 601
    value_type = "behaviour_bus_power_up_down"
    data_type = BehaviourBusPowerUpDown

    @classmethod
    def _to_knx(cls, value: BehaviourBusPowerUpDown) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class DALIFadeTime(DPTEnumData):
    """
    Enum for the DALI fade times.

    DPT 20.602 DPT_DALI_Fade_Time - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    NO_FADE = 0
    FADE_0_7_S = 1
    FADE_1_0_S = 2
    FADE_1_4_S = 3
    FADE_2_0_S = 4
    FADE_2_8_S = 5
    FADE_4_0_S = 6
    FADE_5_7_S = 7
    FADE_8_0_S = 8
    FADE_11_3_S = 9
    FADE_16_0_S = 10
    FADE_22_6_S = 11
    FADE_32_0_S = 12
    FADE_45_3_S = 13
    FADE_64_0_S = 14
    FADE_90_5_S = 15


class DPTDALIFadeTime(DPTEnum[DALIFadeTime]):
    """
    Abstraction for DPT 20.602 DPT_DALI_Fade_Time.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 602
    value_type = "dali_fade_time"
    data_type = DALIFadeTime

    @classmethod
    def _to_knx(cls, value: DALIFadeTime) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BlinkingMode(DPTEnumData):
    """
    Enum for the KNX blinking modes.

    DPT 20.603 DPT_BlinkingMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    DISABLED = 0
    WITHOUT_ACKNOWLEDGE = 1
    WITH_ACKNOWLEDGE = 2


class DPTBlinkingMode(DPTEnum[BlinkingMode]):
    """
    Abstraction for DPT 20.603 DPT_BlinkingMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 603
    value_type = "blinking_mode"
    data_type = BlinkingMode

    @classmethod
    def _to_knx(cls, value: BlinkingMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class LightControlMode(DPTEnumData):
    """
    Enum for the KNX light control modes.

    DPT 20.604 DPT_LightControlMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    AUTOMATIC = 0
    MANUAL = 1


class DPTLightControlMode(DPTEnum[LightControlMode]):
    """
    Abstraction for DPT 20.604 DPT_LightControlMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 604
    value_type = "light_control_mode"
    data_type = LightControlMode

    @classmethod
    def _to_knx(cls, value: LightControlMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class SwitchPBModel(DPTEnumData):
    """
    Enum for the KNX switch push button models; value 0 is reserved.

    DPT 20.605 DPT_SwitchPBModel - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    ONE_PUSH_BUTTON = 1
    TWO_PUSH_BUTTONS = 2


class DPTSwitchPBModel(DPTEnum[SwitchPBModel]):
    """
    Abstraction for DPT 20.605 DPT_SwitchPBModel.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 605
    value_type = "switch_pb_model"
    data_type = SwitchPBModel

    @classmethod
    def _to_knx(cls, value: SwitchPBModel) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class PBAction(DPTEnumData):
    """
    Enum for the KNX push button actions.

    DPT 20.606 DPT_PBAction - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    INACTIVE = 0
    SWITCH_OFF = 1
    SWITCH_ON = 2
    INVERSE_INFO_ON_OFF = 3


class DPTPBAction(DPTEnum[PBAction]):
    """
    Abstraction for DPT 20.606 DPT_PBAction.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 606
    value_type = "pb_action"
    data_type = PBAction

    @classmethod
    def _to_knx(cls, value: PBAction) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class DimmPBModel(DPTEnumData):
    """
    Enum for the KNX dimming push button models; value 0 is reserved.

    DPT 20.607 DPT_DimmPBModel - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    ONE_PUSH_BUTTON_TOGGLE = 1
    ONE_PUSH_BUTTON_ON_DIM_UP = 2
    ONE_PUSH_BUTTON_OFF_DIM_DOWN = 3
    TWO_PUSH_BUTTONS = 4


class DPTDimmPBModel(DPTEnum[DimmPBModel]):
    """
    Abstraction for DPT 20.607 DPT_DimmPBModel.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 607
    value_type = "dimm_pb_model"
    data_type = DimmPBModel

    @classmethod
    def _to_knx(cls, value: DimmPBModel) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class SwitchOnMode(DPTEnumData):
    """
    Enum for the KNX switch on modes.

    DPT 20.608 DPT_SwitchOnMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    LAST_ACTUAL_VALUE = 0
    ADDITIONAL_PARAMETER = 1
    LAST_RECEIVED_ABSOLUTE_SETVALUE = 2


class DPTSwitchOnMode(DPTEnum[SwitchOnMode]):
    """
    Abstraction for DPT 20.608 DPT_SwitchOnMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 608
    value_type = "switch_on_mode"
    data_type = SwitchOnMode

    @classmethod
    def _to_knx(cls, value: SwitchOnMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class LoadTypeSet(DPTEnumData):
    """
    Enum for the KNX dimmer load types to set (CFL: compact fluorescent lamps).

    DPT 20.609 DPT_LoadTypeSet - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    AUTOMATIC = 0
    LEADING_EDGE = 1
    TRAILING_EDGE = 2
    SWITCH_MODE_ONLY = 3
    AUTOMATIC_ONCE = 4
    CFL_LEADING = 5
    CFL_TRAILING = 6
    LED_LEADING = 7
    LED_TRAILING = 8


class DPTLoadTypeSet(DPTEnum[LoadTypeSet]):
    """
    Abstraction for DPT 20.609 DPT_LoadTypeSet.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 609
    value_type = "load_type_set"
    data_type = LoadTypeSet

    @classmethod
    def _to_knx(cls, value: LoadTypeSet) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class LoadTypeDetected(DPTEnumData):
    """
    Enum for the KNX dimmer load types detected (CFL: compact fluorescent lamps).

    DPT 20.610 DPT_LoadTypeDetected - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    UNDEFINED = 0
    LEADING_EDGE = 1
    TRAILING_EDGE = 2
    DETECTION_NOT_POSSIBLE = 3
    CALIBRATION_PENDING = 4
    CFL_LEADING = 5
    CFL_TRAILING = 6
    LED_LEADING = 7
    LED_TRAILING = 8


class DPTLoadTypeDetected(DPTEnum[LoadTypeDetected]):
    """
    Abstraction for DPT 20.610 DPT_LoadTypeDetected.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 610
    value_type = "load_type_detected"
    data_type = LoadTypeDetected

    @classmethod
    def _to_knx(cls, value: LoadTypeDetected) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ConverterTestControl(DPTEnumData):
    """
    Enum for the DALI converter test controls; value 0 is reserved.

    DPT 20.611 DPT_Converter_Test_Control - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §6.3
    """

    START_FUNCTION_TEST = 1
    START_DURATION_TEST = 2
    START_PARTIAL_DURATION_TEST = 3
    STOP_TEST = 4
    RESET_FUNCTION_TEST_DONE_FLAG = 5
    RESET_DURATION_TEST_DONE_FLAG = 6


class DPTConverterTestControl(DPTEnum[ConverterTestControl]):
    """
    Abstraction for DPT 20.611 DPT_Converter_Test_Control.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 611
    value_type = "converter_test_control"
    data_type = ConverterTestControl

    @classmethod
    def _to_knx(cls, value: ConverterTestControl) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ConverterControl(DPTEnumData):
    """
    Enum for the DALI converter controls.

    DPT 20.612 DPT_Converter_Control - KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    RESTORE_FACTORY_DEFAULT_SETTINGS = 0
    GOTO_REST_MODE = 1
    GOTO_INHIBIT_MODE = 2
    RELIGHT_RESET_INHIBIT = 3
    RESET_LAMP_TIME = 4


class DPTConverterControl(DPTEnum[ConverterControl]):
    """
    Abstraction for DPT 20.612 DPT_Converter_Control.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 612
    value_type = "converter_control"
    data_type = ConverterControl

    @classmethod
    def _to_knx(cls, value: ConverterControl) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class ConverterDataRequest(DPTEnumData):
    """
    Enum for the DALI converter data requests; value 0 is reserved.

    DPT 20.613 DPT_Converter_Data_Request - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §6.3
    """

    CONVERTER_STATUS = 1
    CONVERTER_TEST_RESULT = 2
    BATTERY_INFO = 3
    CONVERTER_FT_INFO = 4
    CONVERTER_DT_INFO = 5
    CONVERTER_PDT_INFO = 6
    CONVERTER_INFO = 7
    CONVERTER_INFO_FIX = 8


class DPTConverterDataRequest(DPTEnum[ConverterDataRequest]):
    """
    Abstraction for DPT 20.613 DPT_Converter_Data_Request.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.3
    """

    dpt_main_number = 20
    dpt_sub_number = 613
    value_type = "converter_data_request"
    data_type = ConverterDataRequest

    @classmethod
    def _to_knx(cls, value: ConverterDataRequest) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class SABExceptBehaviour(DPTEnumData):
    """
    Enum for the KNX shutter and blinds exception behaviours.

    DPT 20.801 DPT_SABExcept-Behaviour - KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    UP = 0
    DOWN = 1
    NO_CHANGE = 2
    ADDITIONAL_PARAMETER = 3
    STOP = 4


class DPTSABExceptBehaviour(DPTEnum[SABExceptBehaviour]):
    """
    Abstraction for DPT 20.801 DPT_SABExcept-Behaviour.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    dpt_main_number = 20
    dpt_sub_number = 801
    value_type = "sab_except_behaviour"
    data_type = SABExceptBehaviour

    @classmethod
    def _to_knx(cls, value: SABExceptBehaviour) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class SABBehaviourLockUnlock(DPTEnumData):
    """
    Enum for the KNX shutter and blinds behaviours on locking and unlocking.

    DPT 20.802 DPT_SABBehaviour_Lock_Unlock - KNX v02.02.01 - Datapoint Types 03.07.02 -
    §7.1
    """

    UP = 0
    DOWN = 1
    NO_CHANGE = 2
    ADDITIONAL_PARAMETER = 3
    STOP = 4
    UPDATED_VALUE = 5
    VALUE_BEFORE_LOCKING = 6


class DPTSABBehaviourLockUnlock(DPTEnum[SABBehaviourLockUnlock]):
    """
    Abstraction for DPT 20.802 DPT_SABBehaviour_Lock_Unlock.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    dpt_main_number = 20
    dpt_sub_number = 802
    value_type = "sab_behaviour_lock_unlock"
    data_type = SABBehaviourLockUnlock

    @classmethod
    def _to_knx(cls, value: SABBehaviourLockUnlock) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class SSSBMode(DPTEnumData):
    """
    Enum for the KNX shutter and sun blind push button modes; value 0 is reserved.

    DPT 20.803 DPT_SSSBMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    ONE_PUSH_BUTTON_TOGGLE = 1
    ONE_PUSH_BUTTON_UP = 2
    ONE_PUSH_BUTTON_DOWN = 3
    TWO_PUSH_BUTTONS = 4


class DPTSSSBMode(DPTEnum[SSSBMode]):
    """
    Abstraction for DPT 20.803 DPT_SSSBMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    dpt_main_number = 20
    dpt_sub_number = 803
    value_type = "sssb_mode"
    data_type = SSSBMode

    @classmethod
    def _to_knx(cls, value: SSSBMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class BlindsControlMode(DPTEnumData):
    """
    Enum for the KNX blinds control modes.

    DPT 20.804 DPT_BlindsControlMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    AUTOMATIC = 0
    MANUAL = 1


class DPTBlindsControlMode(DPTEnum[BlindsControlMode]):
    """
    Abstraction for DPT 20.804 DPT_BlindsControlMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §7.1
    """

    dpt_main_number = 20
    dpt_sub_number = 804
    value_type = "blinds_control_mode"
    data_type = BlindsControlMode

    @classmethod
    def _to_knx(cls, value: BlindsControlMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class CommMode(DPTEnumData):
    """
    Enum for the cEMI communication modes (PID_COMM_MODE).

    DPT 20.1000 DPT_CommMode - KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1

    KNX v01.04.02 - External Message Interface 03.06.03 - §4.2.2.4.2 Table 17;
    the other values are reserved or manufacturer specific.
    """

    DATA_LINK_LAYER = 0x00
    DATA_LINK_LAYER_BUSMONITOR = 0x01
    DATA_LINK_LAYER_RAW_FRAMES = 0x02
    CEMI_TRANSPORT_LAYER = 0x06
    NO_LAYER = 0xFF


class DPTCommMode(DPTEnum[CommMode]):
    """
    Abstraction for DPT 20.1000 DPT_CommMode.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    dpt_main_number = 20
    dpt_sub_number = 1000
    value_type = "comm_mode"
    data_type = CommMode

    @classmethod
    def _to_knx(cls, value: CommMode) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class AddInfoType(DPTEnumData):
    """
    Enum for the cEMI additional information types.

    DPT 20.1001 DPT_AddInfoTypes - KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    PL_MEDIUM_DOMAIN_ADDRESS = 0x01
    RF_CONTROL_OCTET_AND_SERIAL_NUMBER_OR_DOA = 0x02
    BUSMONITOR_ERROR_FLAGS = 0x03
    RELATIVE_TIMESTAMP = 0x04
    TIME_DELAY = 0x05
    EXTENDED_RELATIVE_TIMESTAMP = 0x06
    BIBAT_INFORMATION = 0x07


class DPTAddInfoTypes(DPTEnum[AddInfoType]):
    """
    Abstraction for DPT 20.1001 DPT_AddInfoTypes.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    dpt_main_number = 20
    dpt_sub_number = 1001
    value_type = "add_info_types"
    data_type = AddInfoType

    @classmethod
    def _to_knx(cls, value: AddInfoType) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class RFModeSelect(DPTEnumData):
    """
    Enum for the KNX RF mode selection.

    DPT 20.1002 DPT_RF_ModeSelect - KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    ASYNCHRONOUS = 0x00
    ASYNCHRONOUS_BIBAT_MASTER = 0x01
    ASYNCHRONOUS_BIBAT_SLAVE = 0x02


class DPTRFModeSelect(DPTEnum[RFModeSelect]):
    """
    Abstraction for DPT 20.1002 DPT_RF_ModeSelect.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    dpt_main_number = 20
    dpt_sub_number = 1002
    value_type = "rf_mode_select"
    data_type = RFModeSelect

    @classmethod
    def _to_knx(cls, value: RFModeSelect) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


class RFFilterSelect(DPTEnumData):
    """
    Enum for the KNX RF filter modes.

    DPT 20.1003 DPT_RF_FilterSelect - KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    NO_FILTERING = 0x00
    DOMAIN_ADDRESS = 0x01
    SERIAL_NUMBER = 0x02
    DOMAIN_ADDRESS_AND_SERIAL_NUMBER = 0x03


class DPTRFFilterSelect(DPTEnum[RFFilterSelect]):
    """
    Abstraction for DPT 20.1003 DPT_RF_FilterSelect.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.1
    """

    dpt_main_number = 20
    dpt_sub_number = 1003
    value_type = "rf_filter_select"
    data_type = RFFilterSelect

    @classmethod
    def _to_knx(cls, value: RFFilterSelect) -> DPTArray:
        """Return the raw KNX value for an Enum member."""
        return DPTArray(value.value)


@dataclass(slots=True)
class HVACStatus(DPTComplexData):
    """Class for HVACStatus."""

    mode: HVACOperationMode
    dew_point: bool
    heat_cool: HeatCool
    inactive: bool
    frost_alarm: bool

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> HVACStatus:
        """Init from a dictionary."""
        try:
            _mode = data["mode"]
            _heat_cool = data["heat_cool"]
            try:
                mode = HVACOperationMode[_mode.upper()]
                heat_cool = HeatCool[_heat_cool.upper()]
            except AttributeError as err:
                raise ValueError(
                    f"Invalid type for HVAC mode or heat_cool: {err}"
                ) from err
            dew_point = data["dew_point"]
            inactive = data["inactive"]
            frost_alarm = data["frost_alarm"]
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err

        if (
            not isinstance(dew_point, bool)
            or not isinstance(inactive, bool)
            or not isinstance(frost_alarm, bool)
        ):
            raise ValueError(
                f"Invalid value for HVACStatus boolean fields: {dew_point=}, {inactive=}, {frost_alarm=}"
            )

        return cls(
            mode=mode,
            dew_point=dew_point,
            heat_cool=heat_cool,
            inactive=inactive,
            frost_alarm=frost_alarm,
        )

    def as_dict(self) -> dict[str, str | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "mode": self.mode.name.lower(),
            "dew_point": self.dew_point,
            "heat_cool": self.heat_cool.name.lower(),
            "inactive": self.inactive,
            "frost_alarm": self.frost_alarm,
        }


class DPTHVACStatus(DPTComplex[HVACStatus]):
    """
    Abstraction for KNX HVACStatus.

    Non-standardised DP type (in accordance with KNX AN097 “Eberle Status Byte”).
    """

    data_type = HVACStatus
    payload_type = DPTArray
    payload_length = 1
    dpt_main_number = 20
    dpt_sub_number = 60102
    value_type = "hvac_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> HVACStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)[0]

        mode: HVACOperationMode
        if raw & 0x1:
            mode = HVACOperationMode.COMFORT
        elif raw & 0x2:
            mode = HVACOperationMode.STANDBY
        elif raw & 0x4:
            mode = HVACOperationMode.ECONOMY
        elif raw & 0x8:
            mode = HVACOperationMode.BUILDING_PROTECTION
        else:
            mode = HVACOperationMode.AUTO  # not sure if this is possible / valid

        return HVACStatus(
            mode=mode,
            dew_point=bool(raw & 0x10),
            heat_cool=HeatCool.HEAT if raw & 0x20 else HeatCool.COOL,
            inactive=bool(raw & 0x40),
            frost_alarm=bool(raw & 0x80),
        )

    @classmethod
    def _to_knx(cls, value: HVACStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        raw = 0
        if value.mode is HVACOperationMode.COMFORT:
            raw |= 0x1
        elif value.mode is HVACOperationMode.STANDBY:
            raw |= 0x2
        elif value.mode is HVACOperationMode.ECONOMY:
            raw |= 0x4
        elif value.mode is HVACOperationMode.BUILDING_PROTECTION:
            raw |= 0x8
        if value.dew_point:
            raw |= 0x10
        if value.heat_cool is HeatCool.HEAT:
            raw |= 0x20
        if value.inactive:
            raw |= 0x40
        if value.frost_alarm:
            raw |= 0x80
        return DPTArray(raw)
