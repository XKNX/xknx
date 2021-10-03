"""
Implementation of KNX 4 byte Float-values.

They correspond to the the following KDN DPT 14 class.
"""
from __future__ import annotations

from math import ceil, log10
import struct
from typing import cast

from xknx.exceptions import ConversionError

from .dpt import DPTNumeric


class DPT4ByteFloat(DPTNumeric):
    """
    Abstraction for KNX 4 Octet Floating Point Numbers, with a maximum usable range as specified in IEEE 754.

    The largest positive finite float literal is 3.40282347e+38f.
    The smallest positive finite non-zero literal of type float is 1.40239846e-45f.
    The negative minimum finite float literal is -3.40282347e+38f.
    No value range are defined for DPTs 14.000-079.

    DPT 14.***
    """

    dpt_main_number = 14
    dpt_sub_number: int | None = None
    value_type = "4byte_float"
    unit = ""
    payload_length = 4

    value_min = float("-inf")
    value_max = float("inf")
    resolution = 0.0000001

    @classmethod
    def from_knx(cls, raw: tuple[int, ...]) -> float:
        """Parse/deserialize from KNX/IP raw data (big endian)."""
        cls.test_bytesarray(raw)
        try:
            raw_float = cast(float, struct.unpack(">f", bytes(raw))[0])
        except struct.error:
            raise ConversionError(f"Could not parse {cls.__name__}", raw=raw)
        try:
            # round to 7 digit precicion independent of exponent - same value as ETS 5.7 group monitor
            return round(raw_float, 7 - ceil(log10(abs(raw_float))))
        except (ValueError, OverflowError):
            # account for 0 and special values
            # ValueError: log10(0.0); ceil(float('nan'))
            # OverflowError: ceil(float('inf'))
            return raw_float

    @classmethod
    def to_knx(cls, value: float) -> tuple[int, ...]:
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = float(value)
            return tuple(struct.pack(">f", knx_value))
        except (ValueError, struct.error):
            raise ConversionError(f"Could not serialize {cls.__name__}", vlaue=value)


class DPTAcceleration(DPT4ByteFloat):
    """DPT 14.000 DPT_Value_Acceleration (ms-2)."""

    dpt_main_number = 14
    dpt_sub_number = 0
    value_type = "acceleration"
    unit = "m/s²"


class DPTAccelerationAngular(DPT4ByteFloat):
    """DPT 14.001 DPT_Value_Acceleration_Angular (rad s-2)."""

    dpt_main_number = 14
    dpt_sub_number = 1
    value_type = "acceleration_angular"
    unit = "rad/s²"


class DPTActivationEnergy(DPT4ByteFloat):
    """DPT 14.002 DPT_Value_Activation_Energy (J mol-1)."""

    dpt_main_number = 14
    dpt_sub_number = 2
    value_type = "activation_energy"
    unit = "J/mol"


class DPTActivity(DPT4ByteFloat):
    """DPT 14.003 DPT_Value_Activity (s-1)."""

    dpt_main_number = 14
    dpt_sub_number = 3
    value_type = "activity"
    unit = "s⁻¹"


class DPTMol(DPT4ByteFloat):
    """DPT 14.004 DPT_Value_Mol (mol)."""

    dpt_main_number = 14
    dpt_sub_number = 4
    value_type = "mol"
    unit = "mol"


class DPTAmplitude(DPT4ByteFloat):
    """DPT 14.005 DPT_Value_Amplitude."""

    dpt_main_number = 14
    dpt_sub_number = 5
    value_type = "amplitude"
    unit = ""


class DPTAngleRad(DPT4ByteFloat):
    """DPT 14.006 DPT_Value_AngleRad (rad)."""

    dpt_main_number = 14
    dpt_sub_number = 6
    value_type = "angle_rad"
    unit = "rad"


class DPTAngleDeg(DPT4ByteFloat):
    """DPT 14.007 DPT_Value_AngleDeg ((degree))."""

    dpt_main_number = 14
    dpt_sub_number = 7
    value_type = "angle_deg"
    unit = "°"


class DPTAngularMomentum(DPT4ByteFloat):
    """DPT 14.008 DPT_Value_Angular_Momentum (J s)."""

    dpt_main_number = 14
    dpt_sub_number = 8
    value_type = "angular_momentum"
    unit = "J s"


class DPTAngularVelocity(DPT4ByteFloat):
    """DPT 14.009 DPT_Value_Angular_Velocity."""

    dpt_main_number = 14
    dpt_sub_number = 9
    value_type = "angular_velocity"
    unit = "rad/s"


class DPTArea(DPT4ByteFloat):
    """DPT 14.010 DPT_Value_Area."""

    dpt_main_number = 14
    dpt_sub_number = 10
    value_type = "area"
    unit = "m²"


class DPTCapacitance(DPT4ByteFloat):
    """DPT 14.011 DPT_Value_Capacitance."""

    dpt_main_number = 14
    dpt_sub_number = 11
    value_type = "capacitance"
    unit = "F"


class DPTChargeDensitySurface(DPT4ByteFloat):
    """DPT 14.012 DPT_Value_Charge_DensitySurface."""

    dpt_main_number = 14
    dpt_sub_number = 12
    value_type = "charge_density_surface"
    unit = "C/m²"


class DPTChargeDensityVolume(DPT4ByteFloat):
    """DPT 14.013 DPT_Value_Charge_DensityVolume."""

    dpt_main_number = 14
    dpt_sub_number = 13
    value_type = "charge_density_volume"
    unit = "C/m³"


class DPTCompressibility(DPT4ByteFloat):
    """DPT 14.014 DPT_Value_Compressibility."""

    dpt_main_number = 14
    dpt_sub_number = 14
    value_type = "compressibility"
    unit = "m²/N"


class DPTConductance(DPT4ByteFloat):
    """DPT 14.015 DPT_Value_Conductance."""

    dpt_main_number = 14
    dpt_sub_number = 15
    value_type = "conductance"
    unit = "S"


class DPTElectricalConductivity(DPT4ByteFloat):
    """DPT 14.016 DPT_Value_Electrical_Conductivity."""

    dpt_main_number = 14
    dpt_sub_number = 16
    value_type = "electrical_conductivity"
    unit = "S/m"


class DPTDensity(DPT4ByteFloat):
    """DPT 14.017 DPT_Value_Density."""

    dpt_main_number = 14
    dpt_sub_number = 17
    value_type = "density"
    unit = "kg/m³"


class DPTElectricCharge(DPT4ByteFloat):
    """DPT 14.018 DPT_Value_Electric_Charge."""

    dpt_main_number = 14
    dpt_sub_number = 18
    value_type = "electric_charge"
    unit = "C"


class DPTElectricCurrent(DPT4ByteFloat):
    """DPT 14.019 DPT_Value_Electric_Current."""

    dpt_main_number = 14
    dpt_sub_number = 19
    value_type = "electric_current"
    unit = "A"


class DPTElectricCurrentDensity(DPT4ByteFloat):
    """DPT 14.020 DPT_Value_Electric_CurrentDensity."""

    dpt_main_number = 14
    dpt_sub_number = 20
    value_type = "electric_current_density"
    unit = "A/m²"


class DPTElectricDipoleMoment(DPT4ByteFloat):
    """DPT 14.021 DPT_Value_Electric_DipoleMoment."""

    dpt_main_number = 14
    dpt_sub_number = 21
    value_type = "electric_dipole_moment"
    unit = "C m"


class DPTElectricDisplacement(DPT4ByteFloat):
    """DPT 14.022 DPT_Value_Electric_Displacement."""

    dpt_main_number = 14
    dpt_sub_number = 22
    value_type = "electric_displacement"
    unit = "C/m²"


class DPTElectricFieldStrength(DPT4ByteFloat):
    """DPT 14.023 DPT_Value_Electric_FieldStrength."""

    dpt_main_number = 14
    dpt_sub_number = 23
    value_type = "electric_field_strength"
    unit = "V/m"


class DPTElectricFlux(DPT4ByteFloat):
    """DPT 14.024 DPT_Value_Electric_Flux."""

    dpt_main_number = 14
    dpt_sub_number = 24
    value_type = "electric_flux"
    unit = "c"


class DPTElectricFluxDensity(DPT4ByteFloat):
    """DPT 14.025 DPT_Value_Electric_FluxDensity."""

    dpt_main_number = 14
    dpt_sub_number = 25
    value_type = "electric_flux_density"
    unit = "C/m²"


class DPTElectricPolarization(DPT4ByteFloat):
    """DPT 14.026 DPT_Value_Electric_Polarization."""

    dpt_main_number = 14
    dpt_sub_number = 26
    value_type = "electric_polarization"
    unit = "C/m²"


class DPTElectricPotential(DPT4ByteFloat):
    """DPT 14.027 DPT_Value_Electric_Potential."""

    dpt_main_number = 14
    dpt_sub_number = 27
    value_type = "electric_potential"
    unit = "V"


class DPTElectricPotentialDifference(DPT4ByteFloat):
    """DPT 14.028 DPT_Value_Electric_PotentialDifference."""

    dpt_main_number = 14
    dpt_sub_number = 28
    value_type = "electric_potential_difference"
    unit = "V"


class DPTElectromagneticMoment(DPT4ByteFloat):
    """DPT 14.029 DPT_Value_ElectromagneticMoment."""

    dpt_main_number = 14
    dpt_sub_number = 29
    value_type = "electromagnetic_moment"
    unit = "A m²"


class DPTElectromotiveForce(DPT4ByteFloat):
    """DPT 14.030 DPT_Value_Electromotive_Force."""

    dpt_main_number = 14
    dpt_sub_number = 30
    value_type = "electromotive_force"
    unit = "V"


class DPTEnergy(DPT4ByteFloat):
    """DPT 14.031 DPT_Value_Energy."""

    dpt_main_number = 14
    dpt_sub_number = 31
    value_type = "energy"
    unit = "J"


class DPTForce(DPT4ByteFloat):
    """DPT 14.032 DPT_Value_Force."""

    dpt_main_number = 14
    dpt_sub_number = 32
    value_type = "force"
    unit = "N"


class DPTFrequency(DPT4ByteFloat):
    """DPT 14.033 DPT_Value_Frequency."""

    dpt_main_number = 14
    dpt_sub_number = 33
    value_type = "frequency"
    unit = "Hz"


class DPTAngularFrequency(DPT4ByteFloat):
    """DPT 14.034 DPT_Value_Angular_Frequency."""

    dpt_main_number = 14
    dpt_sub_number = 34
    value_type = "angular_frequency"
    unit = "rad/s"


class DPTHeatCapacity(DPT4ByteFloat):
    """DPT 14.035 DPT_Value_Heat_Capacity."""

    dpt_main_number = 14
    dpt_sub_number = 35
    value_type = "heatcapacity"
    unit = "J/K"


class DPTHeatFlowRate(DPT4ByteFloat):
    """DPT 14.036 DPT_Value_Heat_Flow_Rate."""

    dpt_main_number = 14
    dpt_sub_number = 36
    value_type = "heatflowrate"
    unit = "W"


class DPTHeatQuantity(DPT4ByteFloat):
    """DPT 14.037 DPT_Value_Heat_Quantity."""

    dpt_main_number = 14
    dpt_sub_number = 37
    value_type = "heat_quantity"
    unit = "J"


class DPTImpedance(DPT4ByteFloat):
    """DPT 14.038 DPT_Value_Impedance."""

    dpt_main_number = 14
    dpt_sub_number = 38
    value_type = "impedance"
    unit = "Ω"


class DPTLength(DPT4ByteFloat):
    """DPT 14.039 DPT_Value_Length."""

    dpt_main_number = 14
    dpt_sub_number = 39
    value_type = "length"
    unit = "m"


class DPTLightQuantity(DPT4ByteFloat):
    """DPT 14.040 DPT_Value_Light_Quantity."""

    dpt_main_number = 14
    dpt_sub_number = 40
    value_type = "light_quantity"
    unit = "lm s"


class DPTLuminance(DPT4ByteFloat):
    """DPT 14.041 DPT_Value_Luminance."""

    dpt_main_number = 14
    dpt_sub_number = 41
    value_type = "luminance"
    unit = "cd/m²"
    ha_device_class = "illuminance"


class DPTLuminousFlux(DPT4ByteFloat):
    """DPT 14.042 DPT_Value_Heat_Flow_Rate."""

    dpt_main_number = 14
    dpt_sub_number = 42
    value_type = "luminous_flux"
    unit = "lm"
    ha_device_class = "illuminance"


class DPTLuminousIntensity(DPT4ByteFloat):
    """DPT 14.043 DPT_Value_Luminous_Intensity."""

    dpt_main_number = 14
    dpt_sub_number = 43
    value_type = "luminous_intensity"
    unit = "cd"
    ha_device_class = "illuminance"


class DPTMagneticFieldStrength(DPT4ByteFloat):
    """DPT 14.044 DPT_Value_Magnetic_FieldStrength."""

    dpt_main_number = 14
    dpt_sub_number = 44
    value_type = "magnetic_field_strength"
    unit = "A/m"


class DPTMagneticFlux(DPT4ByteFloat):
    """DPT 14.045 DPT_Value_Magnetic_Flux."""

    dpt_main_number = 14
    dpt_sub_number = 45
    value_type = "magnetic_flux"
    unit = "Wb"


class DPTMagneticFluxDensity(DPT4ByteFloat):
    """DPT 14.046 DPT_Value_Magnetic_FluxDensity."""

    dpt_main_number = 14
    dpt_sub_number = 46
    value_type = "magnetic_flux_density"
    unit = "T"


class DPTMagneticMoment(DPT4ByteFloat):
    """DPT 14.047 DPT_Value_Magnetic_Moment."""

    dpt_main_number = 14
    dpt_sub_number = 47
    value_type = "magnetic_moment"
    unit = "A m²"


class DPTMagneticPolarization(DPT4ByteFloat):
    """DPT 14.048 DPT_Value_Magnetic_Polarization."""

    dpt_main_number = 14
    dpt_sub_number = 48
    value_type = "magnetic_polarization"
    unit = "T"


class DPTMagnetization(DPT4ByteFloat):
    """DPT 14.049 DPT_Value_Magnetization."""

    dpt_main_number = 14
    dpt_sub_number = 49
    value_type = "magnetization"
    unit = "A/m"


class DPTMagnetomotiveForce(DPT4ByteFloat):
    """DPT 14.050 DPT_Value_MagnetomotiveForce."""

    dpt_main_number = 14
    dpt_sub_number = 50
    value_type = "magnetomotive_force"
    unit = "A"


class DPTMass(DPT4ByteFloat):
    """DPT 14.051 DPT_Value_Mass."""

    dpt_main_number = 14
    dpt_sub_number = 51
    value_type = "mass"
    unit = "kg"


class DPTMassFlux(DPT4ByteFloat):
    """DPT 14.052 DPT_Value_MassFlux."""

    dpt_main_number = 14
    dpt_sub_number = 52
    value_type = "mass_flux"
    unit = "kg/s"


class DPTMomentum(DPT4ByteFloat):
    """DPT 14.053 DPT_Value_Momentum."""

    dpt_main_number = 14
    dpt_sub_number = 53
    value_type = "momentum"
    unit = "N/s"


class DPTPhaseAngleRad(DPT4ByteFloat):
    """DPT 14.054 DPT_Value_Phase_Angle, Radiant."""

    dpt_main_number = 14
    dpt_sub_number = 54
    value_type = "phaseanglerad"
    unit = "rad"


class DPTPhaseAngleDeg(DPT4ByteFloat):
    """DPT 14.055 DPT_Value_Phase_Angle, Degree."""

    dpt_main_number = 14
    dpt_sub_number = 55
    value_type = "phaseangledeg"
    unit = "°"


class DPTPower(DPT4ByteFloat):
    """DPT 14.056 DPT_Value_Power."""

    dpt_main_number = 14
    dpt_sub_number = 56
    value_type = "power"
    unit = "W"
    ha_device_class = "power"


class DPTPowerFactor(DPT4ByteFloat):
    """DPT 14.057 DPT_Value_Power."""

    dpt_main_number = 14
    dpt_sub_number = 57
    value_type = "powerfactor"
    unit = "cosΦ"
    ha_device_class = "power_factor"


class DPTPressure(DPT4ByteFloat):
    """DPT 14.058 DPT_Value_Pressure."""

    dpt_main_number = 14
    dpt_sub_number = 58
    value_type = "pressure"
    unit = "Pa"
    ha_device_class = "pressure"


class DPTReactance(DPT4ByteFloat):
    """DPT 14.059 DPT_Value_Reactance."""

    dpt_main_number = 14
    dpt_sub_number = 59
    value_type = "reactance"
    unit = "Ω"


class DPTResistance(DPT4ByteFloat):
    """DPT 14.060 DPT_Value_Resistance."""

    dpt_main_number = 14
    dpt_sub_number = 60
    value_type = "resistance"
    unit = "Ω"


class DPTResistivity(DPT4ByteFloat):
    """DPT 14.061 DPT_Value_Resistivity."""

    dpt_main_number = 14
    dpt_sub_number = 61
    value_type = "resistivity"
    unit = "Ω m"


class DPTSelfInductance(DPT4ByteFloat):
    """DPT 14.062 DPT_Value_SelfInductance."""

    dpt_main_number = 14
    dpt_sub_number = 62
    value_type = "self_inductance"
    unit = "H"


class DPTSolidAngle(DPT4ByteFloat):
    """DPT 14.063 DPT_Value_SolidAngle."""

    dpt_main_number = 14
    dpt_sub_number = 63
    value_type = "solid_angle"
    unit = "sr"


class DPTSoundIntensity(DPT4ByteFloat):
    """DPT 14.064 DPT_Value_Sound_Intensity."""

    dpt_main_number = 14
    dpt_sub_number = 64
    value_type = "sound_intensity"
    unit = "W/m²"


class DPTSpeed(DPT4ByteFloat):
    """DPT 14.065 DPT_Value_Speed."""

    dpt_main_number = 14
    dpt_sub_number = 65
    value_type = "speed"
    unit = "m/s"


class DPTStress(DPT4ByteFloat):
    """DPT 14.066 DPT_Value_Stress."""

    dpt_main_number = 14
    dpt_sub_number = 66
    value_type = "stress"
    unit = "Pa"


class DPTSurfaceTension(DPT4ByteFloat):
    """DPT 14.067 DPT_Value_Surface_Tension."""

    dpt_main_number = 14
    dpt_sub_number = 67
    value_type = "surface_tension"
    unit = "N/m"


class DPTCommonTemperature(DPT4ByteFloat):
    """DPT 14.068 DPT_Value_Common_Temperature."""

    dpt_main_number = 14
    dpt_sub_number = 68
    value_type = "common_temperature"
    unit = "°C"


class DPTAbsoluteTemperature(DPT4ByteFloat):
    """DPT 14.069 DPT_Value_Absolute_Temperature."""

    dpt_main_number = 14
    dpt_sub_number = 69
    value_type = "absolute_temperature"
    unit = "K"


class DPTTemperatureDifference(DPT4ByteFloat):
    """DPT 14.070 DPT_Value_TemperatureDifference."""

    dpt_main_number = 14
    dpt_sub_number = 70
    value_type = "temperature_difference"
    unit = "K"


class DPTThermalCapacity(DPT4ByteFloat):
    """DPT 14.071 DPT_Value_Thermal_Capacity."""

    dpt_main_number = 14
    dpt_sub_number = 71
    value_type = "thermal_capacity"
    unit = "J/K"


class DPTThermalConductivity(DPT4ByteFloat):
    """DPT 14.072 DPT_Value_Thermal_Conductivity."""

    dpt_main_number = 14
    dpt_sub_number = 72
    value_type = "thermal_conductivity"
    unit = "W/mK"


class DPTThermoelectricPower(DPT4ByteFloat):
    """DPT 14.073 DPT_Value_ThermoelectricPower."""

    dpt_main_number = 14
    dpt_sub_number = 73
    value_type = "thermoelectric_power"
    unit = "V/K"


class DPTTimeSeconds(DPT4ByteFloat):
    """DPT 14.074 DPT_Value_Time."""

    dpt_main_number = 14
    dpt_sub_number = 74
    value_type = "time_seconds"
    unit = "s"


class DPTTorque(DPT4ByteFloat):
    """DPT 14.075 DPT_Value_Torque."""

    dpt_main_number = 14
    dpt_sub_number = 75
    value_type = "torque"
    unit = "N m"


class DPTVolume(DPT4ByteFloat):
    """DPT 14.076 DPT_Value_Volume."""

    dpt_main_number = 14
    dpt_sub_number = 76
    value_type = "volume"
    unit = "m³"


class DPTVolumeFlux(DPT4ByteFloat):
    """DPT 14.077 DPT_Value_Volume_Flux."""

    dpt_main_number = 14
    dpt_sub_number = 77
    value_type = "volume_flux"
    unit = "m³/s"


class DPTWeight(DPT4ByteFloat):
    """DPT 14.078 DPT_Value_Weight."""

    dpt_main_number = 14
    dpt_sub_number = 78
    value_type = "weight"
    unit = "N"


class DPTWork(DPT4ByteFloat):
    """DPT 14.079 DPT_Value_Work."""

    dpt_main_number = 14
    dpt_sub_number = 79
    value_type = "work"
    unit = "J"
