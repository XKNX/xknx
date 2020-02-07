"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from xknx.dpt import (
    DPT2ByteFloat, DPT2ByteSigned, DPT2ByteUnsigned, DPT2Ucount, DPT4ByteFloat,
    DPT4ByteSigned, DPT4ByteUnsigned, DPTAbsoluteTemperature, DPTAcceleration,
    DPTAccelerationAngular, DPTActivationEnergy, DPTActiveEnergy,
    DPTActiveEnergykWh, DPTActivity, DPTAmplitude, DPTAngle, DPTAngleDeg,
    DPTAngleRad, DPTAngularFrequency, DPTAngularMomentum, DPTAngularVelocity,
    DPTApparantEnergy, DPTApparantEnergykVAh, DPTArea, DPTArray, DPTBrightness,
    DPTCapacitance, DPTChargeDensitySurface, DPTChargeDensityVolume,
    DPTColorTemperature, DPTCommonTemperature, DPTCompressibility,
    DPTConductance, DPTDeltaTimeHrs, DPTDeltaTimeMin, DPTDeltaTimeMsec,
    DPTDeltaTimeSec, DPTDensity, DPTElectricalConductivity, DPTElectricCharge,
    DPTElectricCurrent, DPTElectricCurrentDensity, DPTElectricDipoleMoment,
    DPTElectricDisplacement, DPTElectricFieldStrength, DPTElectricFlux,
    DPTElectricFluxDensity, DPTElectricPolarization, DPTElectricPotential,
    DPTElectricPotentialDifference, DPTElectromagneticMoment,
    DPTElectromotiveForce, DPTEnergy, DPTEnthalpy, DPTFlowRateM3H, DPTForce,
    DPTFrequency, DPTHeatCapacity, DPTHeatFlowRate, DPTHeatQuantity,
    DPTHumidity, DPTImpedance, DPTKelvinPerPercent, DPTLength, DPTLengthMm,
    DPTLightQuantity, DPTLongDeltaTimeSec, DPTLuminance, DPTLuminousFlux,
    DPTLuminousIntensity, DPTLux, DPTMagneticFieldStrength, DPTMagneticFlux,
    DPTMagneticFluxDensity, DPTMagneticMoment, DPTMagneticPolarization,
    DPTMagnetization, DPTMagnetomotiveForce, DPTMass, DPTMassFlux, DPTMol,
    DPTMomentum, DPTPartsPerMillion, DPTPercentU8, DPTPercentV8, DPTPercentV16,
    DPTPhaseAngleDeg, DPTPhaseAngleRad, DPTPower, DPTPower2Byte,
    DPTPowerDensity, DPTPowerFactor, DPTPressure, DPTPressure2Byte,
    DPTRainAmount, DPTReactance, DPTReactiveEnergy, DPTReactiveEnergykVARh,
    DPTResistance, DPTResistivity, DPTRotationAngle, DPTScaling,
    DPTSceneNumber, DPTSelfInductance, DPTSolidAngle, DPTSoundIntensity,
    DPTSpeed, DPTStress, DPTString, DPTSurfaceTension, DPTTemperature,
    DPTTemperatureA, DPTTemperatureDifference, DPTTemperatureDifference2Byte,
    DPTTemperatureF, DPTThermalCapacity, DPTThermalConductivity,
    DPTThermoelectricPower, DPTTime1, DPTTime2, DPTTimePeriod10Msec,
    DPTTimePeriod100Msec, DPTTimePeriodHrs, DPTTimePeriodMin,
    DPTTimePeriodMsec, DPTTimePeriodSec, DPTTimeSeconds, DPTTorque,
    DPTUElCurrentmA, DPTValue1Count, DPTValue1Ucount, DPTValue2Count,
    DPTVoltage, DPTVolume, DPTVolumeFlow, DPTVolumeFlux, DPTWeight, DPTWork,
    DPTWsp, DPTWspKmh)
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueSensor(RemoteValue):
    """Abstraction for many different sensor DPT types."""

    DPTMAP = {
        'absolute_temperature': DPTAbsoluteTemperature,
        'acceleration': DPTAcceleration,
        'acceleration_angular': DPTAccelerationAngular,
        'activation_energy': DPTActivationEnergy,
        'active_energy': DPTActiveEnergy,
        'active_energy_kwh': DPTActiveEnergykWh,
        'activity': DPTActivity,
        'amplitude': DPTAmplitude,
        'angle': DPTAngle,
        'angle_deg': DPTAngleDeg,
        'angle_rad': DPTAngleRad,
        'angular_frequency': DPTAngularFrequency,
        'angular_momentum': DPTAngularMomentum,
        'angular_velocity': DPTAngularVelocity,
        'apparant_energy': DPTApparantEnergy,
        'apparant_energy_kvah': DPTApparantEnergykVAh,
        'area': DPTArea,
        'brightness': DPTBrightness,
        'capacitance': DPTCapacitance,
        'charge_density_surface': DPTChargeDensitySurface,
        'charge_density_volume': DPTChargeDensityVolume,
        'color_temperature': DPTColorTemperature,
        'common_temperature': DPTCommonTemperature,
        'compressibility': DPTCompressibility,
        'conductance': DPTConductance,
        'counter_pulses': DPTValue1Count,
        'current': DPTUElCurrentmA,
        'delta_time_hrs': DPTDeltaTimeHrs,
        'delta_time_min': DPTDeltaTimeMin,
        'delta_time_ms': DPTDeltaTimeMsec,
        'delta_time_sec': DPTDeltaTimeSec,
        'density': DPTDensity,
        'electrical_conductivity': DPTElectricalConductivity,
        'electric_charge': DPTElectricCharge,
        'electric_current': DPTElectricCurrent,
        'electric_current_density': DPTElectricCurrentDensity,
        'electric_dipole_moment': DPTElectricDipoleMoment,
        'electric_displacement': DPTElectricDisplacement,
        'electric_field_strength': DPTElectricFieldStrength,
        'electric_flux': DPTElectricFlux,
        'electric_flux_density': DPTElectricFluxDensity,
        'electric_polarization': DPTElectricPolarization,
        'electric_potential': DPTElectricPotential,
        'electric_potential_difference': DPTElectricPotentialDifference,
        'electromagnetic_moment': DPTElectromagneticMoment,
        'electromotive_force': DPTElectromotiveForce,
        'energy': DPTEnergy,
        'enthalpy': DPTEnthalpy,
        'flow_rate_m3h': DPTFlowRateM3H,
        'force': DPTForce,
        'frequency': DPTFrequency,
        'heatcapacity': DPTHeatCapacity,
        'heatflowrate': DPTHeatFlowRate,
        'heat_quantity': DPTHeatQuantity,
        'humidity': DPTHumidity,
        'impedance': DPTImpedance,
        'illuminance': DPTLux,
        'kelvin_per_percent': DPTKelvinPerPercent,
        'length': DPTLength,
        'length_mm': DPTLengthMm,
        'light_quantity': DPTLightQuantity,
        'long_delta_timesec': DPTLongDeltaTimeSec,
        'luminance': DPTLuminance,
        'luminous_flux': DPTLuminousFlux,
        'luminous_intensity': DPTLuminousIntensity,
        'magnetic_field_strength': DPTMagneticFieldStrength,
        'magnetic_flux': DPTMagneticFlux,
        'magnetic_flux_density': DPTMagneticFluxDensity,
        'magnetic_moment': DPTMagneticMoment,
        'magnetic_polarization': DPTMagneticPolarization,
        'magnetization': DPTMagnetization,
        'magnetomotive_force': DPTMagnetomotiveForce,
        'mass': DPTMass,
        'mass_flux': DPTMassFlux,
        'mol': DPTMol,
        'momentum': DPTMomentum,
        'percent': DPTScaling,
        'percentU8': DPTPercentU8,
        'percentV8': DPTPercentV8,
        'percentV16': DPTPercentV16,
        'phaseanglerad': DPTPhaseAngleRad,
        'phaseangledeg': DPTPhaseAngleDeg,
        'power': DPTPower,
        'power_2byte': DPTPower2Byte,
        'power_density': DPTPowerDensity,
        'powerfactor': DPTPowerFactor,
        'ppm': DPTPartsPerMillion,
        'pressure': DPTPressure,
        'pressure_2byte': DPTPressure2Byte,
        'pulse': DPTValue1Ucount,
        'rain_amount': DPTRainAmount,
        'reactance': DPTReactance,
        'reactive_energy': DPTReactiveEnergy,
        'reactive_energy_kvarh': DPTReactiveEnergykVARh,
        'resistance': DPTResistance,
        'resistivity': DPTResistivity,
        'rotation_angle': DPTRotationAngle,
        'scene_number': DPTSceneNumber,
        'self_inductance': DPTSelfInductance,
        'solid_angle': DPTSolidAngle,
        'sound_intensity': DPTSoundIntensity,
        'speed': DPTSpeed,
        'stress': DPTStress,
        'surface_tension': DPTSurfaceTension,
        'string': DPTString,
        'temperature': DPTTemperature,
        'temperature_a': DPTTemperatureA,
        'temperature_difference': DPTTemperatureDifference,
        'temperature_difference_2byte': DPTTemperatureDifference2Byte,
        'temperature_f': DPTTemperatureF,
        'thermal_capacity': DPTThermalCapacity,
        'thermal_conductivity': DPTThermalConductivity,
        'thermoelectric_power': DPTThermoelectricPower,
        'time_1': DPTTime1,
        'time_2': DPTTime2,
        'time_period_100msec': DPTTimePeriod100Msec,
        'time_period_10msec': DPTTimePeriod10Msec,
        'time_period_hrs': DPTTimePeriodHrs,
        'time_period_min': DPTTimePeriodMin,
        'time_period_msec': DPTTimePeriodMsec,
        'time_period_sec': DPTTimePeriodSec,
        'time_seconds': DPTTimeSeconds,
        'torque': DPTTorque,
        'voltage': DPTVoltage,
        'volume': DPTVolume,
        'volume_flow': DPTVolumeFlow,
        'volume_flux': DPTVolumeFlux,
        'weight': DPTWeight,
        'work': DPTWork,
        'wind_speed_ms': DPTWsp,
        'wind_speed_kmh': DPTWspKmh,
        # Generic DPT Without Min/Max and Unit.
        'DPT-5': DPTValue1Ucount,
        '1byte_unsigned': DPTValue1Ucount,
        # Generic 2 byte DPT
        'DPT-7': DPT2ByteUnsigned,
        '2byte_unsigned': DPT2Ucount,
        'DPT-8': DPT2ByteSigned,
        '2byte_signed': DPTValue2Count,
        'DPT-9': DPT2ByteFloat,
        # Generic 4 byte DPT
        'DPT-12': DPT4ByteUnsigned,
        '4byte_unsigned': DPT4ByteUnsigned,
        'DPT-13': DPT4ByteSigned,
        '4byte_signed': DPT4ByteSigned,
        'DPT-14': DPT4ByteFloat,
        '4byte_float': DPT4ByteFloat
    }

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 sync_state=True,
                 value_type=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize RemoteValueSensor class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx,
                         group_address,
                         group_address_state,
                         sync_state=sync_state,
                         device_name=device_name,
                         after_update_cb=after_update_cb)
        if value_type not in self.DPTMAP:
            raise ConversionError("invalid value type", value_type=value_type, device_name=device_name)
        self.value_type = value_type

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed."""
        return (
            isinstance(payload, DPTArray) and
            len(payload.value) == self.DPTMAP[self.value_type].payload_length)

    def to_knx(self, value):
        """Convert value to payload."""
        return DPTArray(self.DPTMAP[self.value_type].to_knx(value))

    def from_knx(self, payload):
        """Convert current payload to value."""
        return self.DPTMAP[self.value_type].from_knx(payload.value)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.DPTMAP[self.value_type].unit

    @property
    def ha_device_class(self):
        """Return a string representing the home assistant device class."""
        if hasattr(self.DPTMAP[self.value_type], 'ha_device_class'):
            return self.DPTMAP[self.value_type].ha_device_class
        return None
