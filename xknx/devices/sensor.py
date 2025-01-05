"""
Module for managing a sensor via KNX.

It provides functionality for

* reading the current state from KNX bus.
* watching for state updates from KNX bus.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from xknx.dpt import (
    DPT2ByteFloat,
    DPT2ByteSigned,
    DPT2ByteUnsigned,
    DPT2Ucount,
    DPT4ByteFloat,
    DPT4ByteSigned,
    DPT4ByteUnsigned,
    DPT8ByteSigned,
    DPTAbsoluteHumidity,
    DPTAbsoluteTemperature,
    DPTAcceleration,
    DPTAccelerationAngular,
    DPTActivationEnergy,
    DPTActiveEnergy,
    DPTActiveEnergy8Byte,
    DPTActiveEnergykWh,
    DPTActiveEnergyMWh,
    DPTActivity,
    DPTAirFlow,
    DPTAmplitude,
    DPTAngle,
    DPTAngleDeg,
    DPTAngleRad,
    DPTAngularFrequency,
    DPTAngularMomentum,
    DPTAngularVelocity,
    DPTApparantEnergy,
    DPTApparantEnergy8Byte,
    DPTApparantEnergykVAh,
    DPTApparentPower,
    DPTArea,
    DPTBase,
    DPTBrightness,
    DPTCapacitance,
    DPTChargeDensitySurface,
    DPTChargeDensityVolume,
    DPTColorTemperature,
    DPTCommonTemperature,
    DPTCompressibility,
    DPTConcentrationUGM3,
    DPTConductance,
    DPTCurrent,
    DPTDecimalFactor,
    DPTDeltaTime10Msec,
    DPTDeltaTime100Msec,
    DPTDeltaTimeHrs,
    DPTDeltaTimeMin,
    DPTDeltaTimeMsec,
    DPTDeltaTimeSec,
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
    DPTEnthalpy,
    DPTFlowRateM3H,
    DPTForce,
    DPTFrequency,
    DPTHeatCapacity,
    DPTHeatFlowRate,
    DPTHeatQuantity,
    DPTHumidity,
    DPTImpedance,
    DPTKelvinPerPercent,
    DPTLatin1,
    DPTLength,
    DPTLengthM,
    DPTLengthMm,
    DPTLightQuantity,
    DPTLongDeltaTimeSec,
    DPTLongTimePeriodHrs,
    DPTLongTimePeriodMin,
    DPTLongTimePeriodSec,
    DPTLuminance,
    DPTLuminousFlux,
    DPTLuminousIntensity,
    DPTLux,
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
    DPTPartsPerMillion,
    DPTPercentU8,
    DPTPercentV8,
    DPTPercentV16,
    DPTPhaseAngleDeg,
    DPTPhaseAngleRad,
    DPTPower,
    DPTPower2Byte,
    DPTPowerDensity,
    DPTPowerFactor,
    DPTPressure,
    DPTPressure2Byte,
    DPTRainAmount,
    DPTReactance,
    DPTReactiveEnergy,
    DPTReactiveEnergy8Byte,
    DPTReactiveEnergykVARh,
    DPTResistance,
    DPTResistivity,
    DPTRotationAngle,
    DPTScaling,
    DPTSceneNumber,
    DPTSelfInductance,
    DPTSignedRelativeValue,
    DPTSolidAngle,
    DPTSoundIntensity,
    DPTSpeed,
    DPTStress,
    DPTString,
    DPTSurfaceTension,
    DPTTariff,
    DPTTemperature,
    DPTTemperatureA,
    DPTTemperatureDifference,
    DPTTemperatureDifference2Byte,
    DPTTemperatureF,
    DPTThermalCapacity,
    DPTThermalConductivity,
    DPTThermoelectricPower,
    DPTTime1,
    DPTTime2,
    DPTTimePeriod10Msec,
    DPTTimePeriod100Msec,
    DPTTimePeriodHrs,
    DPTTimePeriodMin,
    DPTTimePeriodMsec,
    DPTTimePeriodSec,
    DPTTimeSeconds,
    DPTTorque,
    DPTUElCurrentmA,
    DPTValue1ByteUnsigned,
    DPTValue1Count,
    DPTValue1Ucount,
    DPTValue2Count,
    DPTValue4Count,
    DPTValue4Ucount,
    DPTVoltage,
    DPTVolume,
    DPTVolumeFlow,
    DPTVolumeFlux,
    DPTVolumeLiquidLitre,
    DPTVolumeM3,
    DPTWeight,
    DPTWork,
    DPTWsp,
    DPTWspKmh,
)
from xknx.exceptions.exception import DeviceIllegalValue
from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueSensor,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class Sensor(Device):
    """Class for managing a sensor."""

    supported_dpts: tuple[type[DPTBase], ...] = (
        DPTValue1ByteUnsigned,
        DPTScaling,
        DPTAngle,
        DPTPercentU8,
        DPTDecimalFactor,
        DPTTariff,
        DPTValue1Ucount,
        DPTSignedRelativeValue,
        DPTPercentV8,
        DPTValue1Count,
        DPT2ByteUnsigned,
        DPT2Ucount,
        DPTTimePeriodMsec,
        DPTTimePeriod10Msec,
        DPTTimePeriod100Msec,
        DPTTimePeriodSec,
        DPTTimePeriodMin,
        DPTTimePeriodHrs,
        DPTLengthMm,
        DPTUElCurrentmA,
        DPTBrightness,
        DPTColorTemperature,
        DPT2ByteSigned,
        DPTValue2Count,
        DPTDeltaTimeMsec,
        DPTDeltaTime10Msec,
        DPTDeltaTime100Msec,
        DPTDeltaTimeSec,
        DPTDeltaTimeMin,
        DPTDeltaTimeHrs,
        DPTPercentV16,
        DPTRotationAngle,
        DPTLengthM,
        DPT2ByteFloat,
        DPTTemperature,
        DPTTemperatureDifference2Byte,
        DPTTemperatureA,
        DPTLux,
        DPTWsp,
        DPTPressure2Byte,
        DPTHumidity,
        DPTPartsPerMillion,
        DPTAirFlow,
        DPTTime1,
        DPTTime2,
        DPTVoltage,
        DPTCurrent,
        DPTPowerDensity,
        DPTKelvinPerPercent,
        DPTPower2Byte,
        DPTVolumeFlow,
        DPTRainAmount,
        DPTTemperatureF,
        DPTWspKmh,
        DPTAbsoluteHumidity,
        DPTConcentrationUGM3,
        DPTEnthalpy,
        DPT4ByteUnsigned,
        DPTValue4Ucount,
        DPTLongTimePeriodSec,
        DPTLongTimePeriodMin,
        DPTLongTimePeriodHrs,
        DPTVolumeLiquidLitre,
        DPTVolumeM3,
        DPT4ByteSigned,
        DPTValue4Count,
        DPTFlowRateM3H,
        DPTActiveEnergy,
        DPTApparantEnergy,
        DPTReactiveEnergy,
        DPTActiveEnergykWh,
        DPTApparantEnergykVAh,
        DPTReactiveEnergykVARh,
        DPTActiveEnergyMWh,
        DPTLongDeltaTimeSec,
        DPT4ByteFloat,
        DPTAcceleration,
        DPTAccelerationAngular,
        DPTActivationEnergy,
        DPTActivity,
        DPTMol,
        DPTAmplitude,
        DPTAngleRad,
        DPTAngleDeg,
        DPTAngularMomentum,
        DPTAngularVelocity,
        DPTArea,
        DPTCapacitance,
        DPTChargeDensitySurface,
        DPTChargeDensityVolume,
        DPTCompressibility,
        DPTConductance,
        DPTElectricalConductivity,
        DPTDensity,
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
        DPTAngularFrequency,
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
        DPTMomentum,
        DPTPhaseAngleRad,
        DPTPhaseAngleDeg,
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
        DPTCommonTemperature,
        DPTAbsoluteTemperature,
        DPTTemperatureDifference,
        DPTThermalCapacity,
        DPTThermalConductivity,
        DPTThermoelectricPower,
        DPTTimeSeconds,
        DPTTorque,
        DPTVolume,
        DPTVolumeFlux,
        DPTWeight,
        DPTWork,
        DPTApparentPower,
        DPTString,
        DPTLatin1,
        DPTSceneNumber,
        DPT8ByteSigned,
        DPTActiveEnergy8Byte,
        DPTApparantEnergy8Byte,
        DPTReactiveEnergy8Byte,
    )

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        always_callback: bool = False,
        value_type: int | str | None = None,
        device_updated_cb: DeviceCallbackType[Sensor] | None = None,
    ):
        """Initialize Sensor class."""
        super().__init__(xknx, name, device_updated_cb)

        if value_type is not None and not self.validate_value_type(value_type):
            raise DeviceIllegalValue(
                value_type,
                f"value_type '{value_type}' not supported. Supported types are: "
                f"{[dpt.value_type for dpt in self.supported_dpts]}",
            )

        self.sensor_value = RemoteValueSensor(
            xknx,
            group_address_state=group_address_state,
            sync_state=sync_state,
            value_type=value_type,
            device_name=self.name,
            after_update_cb=self.after_update,
        )
        self.always_callback = always_callback

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    @property
    def last_telegram(self) -> Telegram | None:
        """Return the last telegram received from the RemoteValue."""
        return self.sensor_value.telegram

    def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        self.sensor_value.process(telegram, always_callback=self.always_callback)

    def process_group_response(self, telegram: Telegram) -> None:
        """Process incoming GroupValueResponse telegrams."""
        self.sensor_value.process(telegram)

    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def ha_device_class(self) -> str | None:
        """Return the home assistant device class as string."""
        return self.sensor_value.ha_device_class

    def resolve_state(self) -> Any | None:
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    @classmethod
    def transcode_dpt_to_value_type(cls, dpt_id: str) -> int | str | None:
        """Transcode DPT string to value type or return None if not supported."""
        if not (dpt_cls := DPTBase.parse_transcoder(dpt_id)):
            return None
        return next(
            (dpt.value_type for dpt in cls.supported_dpts if dpt == dpt_cls), None
        )

    @classmethod
    def validate_value_type(cls, value_type: int | str) -> bool:
        """Return True if value type is supported."""
        return any(dpt.value_type == value_type for dpt in cls.supported_dpts)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Sensor name="{self.name}" '
            f"sensor={self.sensor_value.group_addr_str()} "
            f"value={self.resolve_state().__repr__()} "
            f'unit="{self.unit_of_measurement()}"/>'
        )
