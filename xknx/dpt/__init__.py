"""
Module for encoding and decoding KNX datatypes.

* KNX Values like Int, Float, String, Time
* Derived KNX Values like Scaling, Temperature
"""

# ruff: noqa: F401
from .dpt import (
    DPTBase,
    DPTComplex,
    DPTComplexData,
    DPTComplexFieldSchema,
    DPTEnum,
    DPTEnumData,
    DPTNumeric,
)
from .dpt_1 import (
    DPT1BitBoolean,
    DPTAck,
    DPTAlarm,
    DPTBinaryValue,
    DPTBool,
    DPTConsumerProducer,
    DPTDayNight,
    DPTDimSendStyle,
    DPTEnable,
    DPTEnergyDirection,
    DPTHeatCool,
    DPTInputSource,
    DPTInvert,
    DPTLogicalFunction,
    DPTOccupancy,
    DPTOpenClose,
    DPTRamp,
    DPTReset,
    DPTSceneAB,
    DPTShutterBlindsMode,
    DPTStart,
    DPTState,
    DPTStep,
    DPTSwitch,
    DPTTrigger,
    DPTUpDown,
    DPTWindowDoor,
)
from .dpt_2 import (
    DPT2BitBoolean,
    DPTAlarmControl,
    DPTBinaryValueControl,
    DPTBoolControl,
    DPTDirection1Control,
    DPTDirection2Control,
    DPTEnableControl,
    DPTInvertControl,
    DPTRampControl,
    DPTStartControl,
    DPTStateControl,
    DPTStepControl,
    DPTSwitchControl,
)
from .dpt_3 import DPTControlBlinds, DPTControlDimming
from .dpt_4 import DPTCharacter, DPTCharacterLatin1
from .dpt_5 import (
    DPTAngle,
    DPTDecimalFactor,
    DPTPercentU8,
    DPTScaling,
    DPTTariff,
    DPTValue1ByteUnsigned,
    DPTValue1Ucount,
)
from .dpt_6 import DPTPercentV8, DPTSignedRelativeValue, DPTValue1Count
from .dpt_7 import (
    DPT2ByteUnsigned,
    DPT2Ucount,
    DPTBrightness,
    DPTColorTemperature,
    DPTLengthMm,
    DPTPropDataType,
    DPTTimePeriod10Msec,
    DPTTimePeriod100Msec,
    DPTTimePeriodHrs,
    DPTTimePeriodMin,
    DPTTimePeriodMsec,
    DPTTimePeriodSec,
    DPTUElCurrentmA,
)
from .dpt_8 import (
    DPT2ByteSigned,
    DPTDeltaTime10Msec,
    DPTDeltaTime100Msec,
    DPTDeltaTimeHrs,
    DPTDeltaTimeMin,
    DPTDeltaTimeMsec,
    DPTDeltaTimeSec,
    DPTLengthM,
    DPTPercentV16,
    DPTRotationAngle,
    DPTValue2Count,
)
from .dpt_9 import (
    DPT2ByteFloat,
    DPTAbsoluteHumidity,
    DPTAirFlow,
    DPTConcentrationUGM3,
    DPTCurrent,
    DPTEnthalpy,
    DPTHumidity,
    DPTKelvinPerPercent,
    DPTLux,
    DPTPartsPerMillion,
    DPTPower2Byte,
    DPTPowerDensity,
    DPTPressure2Byte,
    DPTRainAmount,
    DPTTemperature,
    DPTTemperatureA,
    DPTTemperatureDifference2Byte,
    DPTTemperatureF,
    DPTTime1,
    DPTTime2,
    DPTVoltage,
    DPTVolumeFlow,
    DPTWsp,
    DPTWspKmh,
)
from .dpt_10 import DPTTime
from .dpt_11 import DPTDate
from .dpt_12 import (
    DPT4ByteUnsigned,
    DPTLongTimePeriodHrs,
    DPTLongTimePeriodMin,
    DPTLongTimePeriodSec,
    DPTValue4Ucount,
    DPTVolumeLiquidLitre,
    DPTVolumeM3,
)
from .dpt_13 import (
    DPT4ByteSigned,
    DPTActiveEnergy,
    DPTActiveEnergykWh,
    DPTActiveEnergyMWh,
    DPTApparantEnergy,
    DPTApparantEnergykVAh,
    DPTDeltaVolumeLiquidLitre,
    DPTDeltaVolumeM3,
    DPTFlowRateM3H,
    DPTLongDeltaTimeSec,
    DPTReactiveEnergy,
    DPTReactiveEnergykVARh,
    DPTValue4Count,
)
from .dpt_14 import (
    DPT4ByteFloat,
    DPTAbsoluteTemperature,
    DPTAcceleration,
    DPTAccelerationAngular,
    DPTActivationEnergy,
    DPTActivity,
    DPTAmplitude,
    DPTAngleDeg,
    DPTAngleRad,
    DPTAngularFrequency,
    DPTAngularMomentum,
    DPTAngularVelocity,
    DPTApparentPower,
    DPTArea,
    DPTCapacitance,
    DPTChargeDensitySurface,
    DPTChargeDensityVolume,
    DPTCommonTemperature,
    DPTCompressibility,
    DPTConductance,
    DPTDensity,
    DPTElectricalConductivity,
    DPTElectricCharge,
    DPTElectricCurrent,
    DPTElectricCurrentDensity,
    DPTElectricDipoleMoment,
    DPTElectricDisplacement,
    DPTElectricFieldStrength,
    DPTElectricFlux,
    DPTElectricFluxDensity,
    DPTElectricPolarization,
    DPTElectricPotential,
    DPTElectricPotentialDifference,
    DPTElectromagneticMoment,
    DPTElectromotiveForce,
    DPTEnergy,
    DPTForce,
    DPTFrequency,
    DPTHeatCapacity,
    DPTHeatFlowRate,
    DPTHeatQuantity,
    DPTImpedance,
    DPTLength,
    DPTLightQuantity,
    DPTLuminance,
    DPTLuminousFlux,
    DPTLuminousIntensity,
    DPTMagneticFieldStrength,
    DPTMagneticFlux,
    DPTMagneticFluxDensity,
    DPTMagneticMoment,
    DPTMagneticPolarization,
    DPTMagnetization,
    DPTMagnetomotiveForce,
    DPTMass,
    DPTMassFlux,
    DPTMol,
    DPTMomentum,
    DPTPhaseAngleDeg,
    DPTPhaseAngleRad,
    DPTPower,
    DPTPowerFactor,
    DPTPressure,
    DPTReactance,
    DPTResistance,
    DPTResistivity,
    DPTSelfInductance,
    DPTSolidAngle,
    DPTSoundIntensity,
    DPTSpeed,
    DPTStress,
    DPTSurfaceTension,
    DPTTemperatureDifference,
    DPTThermalCapacity,
    DPTThermalConductivity,
    DPTThermoelectricPower,
    DPTTimeSeconds,
    DPTTorque,
    DPTVolume,
    DPTVolumeFlux,
    DPTVolumeFluxLs,
    DPTVolumeFluxMeter,
    DPTWeight,
    DPTWork,
)
from .dpt_15 import AccessData, DPTAccessData
from .dpt_16 import DPTLatin1, DPTString
from .dpt_17 import DPTSceneNumber
from .dpt_18 import DPTSceneControl, SceneControl
from .dpt_19 import DPTDateTime
from .dpt_20 import DPTErrorClassSystem, DPTHVACContrMode, DPTHVACMode, DPTHVACStatus
from .dpt_21 import (
    ChannelActivation8,
    DeviceControl,
    DPTChannelActivation8,
    DPTDeviceControl,
    DPTForceSign,
    DPTForceSignCool,
    DPTFuelTypeSet,
    DPTLightActuatorErrorInfo,
    DPTPhasesStatus,
    DPTRFFilterInfo,
    DPTRFModeInfo,
    DPTSecurityReport,
    DPTStatusAHU,
    DPTStatusGen,
    DPTStatusRCC,
    DPTStatusRHC,
    DPTStatusSDHWC,
    DPTVirtualDryContact,
    ForcingSignal,
    ForcingSignalCool,
    FuelTypeSet,
    GeneralStatus,
    LightActuatorErrorInfo,
    PhasesStatus,
    RFFilterInfo,
    RFModeInfo,
    RoomCoolingControllerStatus,
    RoomHeatingControllerStatus,
    SecurityReport,
    SolarDHWControllerStatus,
    VentilationControllerStatus,
    VirtualDryContact,
)
from .dpt_22 import (
    ChannelActivation16,
    DHWControllerStatus,
    DPTChannelActivation16,
    DPTMedia,
    DPTStatusDHWC,
    DPTStatusRHCC,
    RoomHeatingCoolingControllerStatus,
    SupportedMedia,
)
from .dpt_25 import DoubleNibble, DPTDoubleNibble
from .dpt_26 import DPTSceneInfo, SceneInfo
from .dpt_27 import CombinedInfoOnOff, DPTCombinedInfoOnOff
from .dpt_29 import (
    DPT8ByteSigned,
    DPTActiveEnergy8Byte,
    DPTApparantEnergy8Byte,
    DPTReactiveEnergy8Byte,
)
from .dpt_30 import ChannelActivation24, DPTChannelActivation24
from .dpt_206 import (
    BuildingModeNext,
    DHWModeNext,
    DPTBuildingModeNext,
    DPTDHWModeNext,
    DPTHVACModeNext,
    DPTOccModeNext,
    HVACModeNext,
    OccupancyModeNext,
)
from .dpt_207 import (
    ActuatorPositionDemand,
    ActuatorPositionStatus,
    BoilerControllerDemand,
    BurnerControllerStatus,
    DPTActPosDemAbs,
    DPTLockSign,
    DPTStatusAct,
    DPTStatusBUC,
    DPTStatusLightingActuator,
    DPTValueDemBOC,
    LightingActuatorStatus,
    LockingSignal,
)
from .dpt_219 import AlarmInfo, DPTAlarmInfo
from .dpt_222 import (
    DPTRoomTemperatureSetpoints3,
    DPTRoomTemperatureSetpointShifts3,
    RoomTemperatureSetpoints3,
    RoomTemperatureSetpointShifts3,
)
from .dpt_225 import (
    DPTScalingSpeed,
    DPTScalingStepTime,
    ScalingSpeed,
    ScalingStepTime,
)
from .dpt_229 import DPTMeteringValue, MeteringValue, MeteringValueUnit
from .dpt_230 import DPTMBusAddress, MBusAddress
from .dpt_232 import DPTColorRGB, RGBColor
from .dpt_234 import DPTLanguageCodeAlpha2ASCII, DPTRegionCodeAlpha2ASCII
from .dpt_235 import DPTTariffActiveEnergy, TariffActiveEnergy
from .dpt_236 import DPTPrioritisedModeControl, PrioritisedModeControl
from .dpt_237 import (
    DALIAddressIndicator,
    DALIControlGearDiagnostic,
    DPTDALIControlGearDiagnostic,
)
from .dpt_238 import DALIDiagnostics, DPTDALIDiagnostics, DPTSceneConfig, SceneConfig
from .dpt_240 import CombinedPosition, DPTCombinedPosition
from .dpt_241 import DPTStatusSAB, StatusSAB
from .dpt_242 import DPTColorXYY, XYYColor
from .dpt_243 import DPTColorXYYTransition, XYYColorTransition
from .dpt_244 import (
    ConverterFailure,
    ConverterMode,
    ConverterStatus,
    ConverterTestPending,
    DPTConverterStatus,
)
from .dpt_245 import (
    ConverterTestResult,
    ConverterTestResultCode,
    ConverterTestStartMethod,
    DPTConverterTestResult,
)
from .dpt_246 import BatteryInfo, DPTBatteryInfo
from .dpt_247 import ConverterTestInfo, DPTConverterTestInfo
from .dpt_248 import ConverterInfoFix, ConverterInfoValid, DPTConverterInfoFix
from .dpt_249 import ColorTemperatureTransition, DPTColorTemperatureTransition
from .dpt_250 import ColorTemperatureControl, DPTColorTemperatureControl
from .dpt_251 import DPTColorRGBW, RGBWColor
from .dpt_252 import DPTRelativeControlRGBW, RelativeControlRGBW
from .dpt_253 import DPTRelativeControlXYY, RelativeControlXYY
from .dpt_254 import DPTRelativeControlRGB, RelativeControlRGB
from .dpt_255 import DPTGeographicalLocation, GeographicalLocation
from .dpt_272 import ConverterInfo, DPTConverterInfo
from .dpt_273 import (
    DPTForecastAbsoluteHumidity,
    DPTForecastAirPollutants,
    DPTForecastCO2,
    DPTForecastRelativeHumidity,
    DPTForecastSunIntensity,
    DPTForecastTemperature,
    DPTForecastWindSpeed,
    Forecast,
)
from .dpt_275 import (
    DPTRoomTemperatureSetpoints4,
    DPTRoomTemperatureSetpointShifts4,
    RoomTemperatureSetpoints4,
    RoomTemperatureSetpointShifts4,
)
from .payload import DPTArray, DPTBinary
