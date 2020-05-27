"""
Implementation of KNX 4 byte Float-values.

They correspond to the the following KDN DPT 14 class.
"""

import struct

from xknx.exceptions import ConversionError

from .dpt import DPTBase


class DPT4ByteFloat(DPTBase):
    """
    Abstraction for KNX 4 Octet Floating Point Numbers, with a maximum usable range as specified in IEEE 754.

    The largest positive finite float literal is 3.40282347e+38f.
    The smallest positive finite non-zero literal of type float is 1.40239846e-45f.
    The negative minimum finite float literal is -3.40282347e+38f.
    No value range are defined for DPTs 14.000-079.

    DPT 14.***
    """

    unit = ""
    payload_length = 4

    @classmethod
    def from_knx(cls, raw):
        """Parse/deserialize from KNX/IP raw data (big endian)."""
        cls.test_bytesarray(raw, 4)
        try:
            return struct.unpack(">f", bytes(raw))[0]
        except struct.error:
            raise ConversionError("Cant parse %s" % cls.__name__, raw=raw)

    @classmethod
    def to_knx(cls, value):
        """Serialize to KNX/IP raw data."""
        try:
            knx_value = float(value)
            return tuple(struct.pack(">f", knx_value))
        except (ValueError, struct.error):
            raise ConversionError("Cant serialize %s" % cls.__name__, vlaue=value)


class DPTAcceleration(DPT4ByteFloat):
    """DPT 14.000 DPT_Value_Acceleration (ms-2)."""

    unit = "m/s²"


class DPTAccelerationAngular(DPT4ByteFloat):
    """DPT 14.001 DPT_Value_Acceleration_Angular (rad s-2)."""

    unit = "rad/s²"


class DPTActivationEnergy(DPT4ByteFloat):
    """DPT 14.002 DPT_Value_Activation_Energy (J mol-1)."""

    unit = "J/mol"


class DPTActivity(DPT4ByteFloat):
    """DPT 14.003 DPT_Value_Activity (s-1)."""

    unit = "s⁻¹"


class DPTMol(DPT4ByteFloat):
    """DPT 14.004 DPT_Value_Mol (mol)."""

    unit = "mol"


class DPTAmplitude(DPT4ByteFloat):
    """DPT 14.005 DPT_Value_Amplitude."""


class DPTAngleRad(DPT4ByteFloat):
    """DPT 14.006 DPT_Value_AngleRad (rad)."""

    unit = "rad"


class DPTAngleDeg(DPT4ByteFloat):
    """DPT 14.007 DPT_Value_AngleDeg ((degree))."""

    unit = "°"


class DPTAngularMomentum(DPT4ByteFloat):
    """DPT 14.008 DPT_Value_Angular_Momentum (J s)."""

    unit = "J s"


class DPTAngularVelocity(DPT4ByteFloat):
    """DPT 14.009 DPT_Value_Angular_Velocity."""

    unit = "rad/s"


class DPTArea(DPT4ByteFloat):
    """DPT 14.010 DPT_Value_Area."""

    unit = "m²"


class DPTCapacitance(DPT4ByteFloat):
    """DPT 14.011 DPT_Value_Capacitance."""

    unit = "F"


class DPTChargeDensitySurface(DPT4ByteFloat):
    """DPT 14.012 DPT_Value_Charge_DensitySurface."""

    unit = "C/m²"


class DPTChargeDensityVolume(DPT4ByteFloat):
    """DPT 14.013 DPT_Value_Charge_DensityVolume."""

    unit = "C/m³"


class DPTCompressibility(DPT4ByteFloat):
    """DPT 14.014 DPT_Value_Compressibility."""

    unit = "m²/N"


class DPTConductance(DPT4ByteFloat):
    """DPT 14.015 DPT_Value_Conductance."""

    unit = "S"


class DPTElectricalConductivity(DPT4ByteFloat):
    """DPT 14.016 DPT_Value_Electrical_Conductivity."""

    unit = "S/m"


class DPTDensity(DPT4ByteFloat):
    """DPT 14.017 DPT_Value_Density."""

    unit = "kg/m³"


class DPTElectricCharge(DPT4ByteFloat):
    """DPT 14.018 DPT_Value_Electric_Charge."""

    unit = "C"


class DPTElectricCurrent(DPT4ByteFloat):
    """DPT 14.019 DPT_Value_Electric_Current."""

    unit = "A"


class DPTElectricCurrentDensity(DPT4ByteFloat):
    """DPT 14.020 DPT_Value_Electric_CurrentDensity."""

    unit = "A/m²"


class DPTElectricDipoleMoment(DPT4ByteFloat):
    """DPT 14.021 DPT_Value_Electric_DipoleMoment."""

    unit = "C m"


class DPTElectricDisplacement(DPT4ByteFloat):
    """DPT 14.022 DPT_Value_Electric_Displacement."""

    unit = "C/m²"


class DPTElectricFieldStrength(DPT4ByteFloat):
    """DPT 14.023 DPT_Value_Electric_FieldStrength."""

    unit = "V/m"


class DPTElectricFlux(DPT4ByteFloat):
    """DPT 14.024 DPT_Value_Electric_Flux."""

    unit = "c"


class DPTElectricFluxDensity(DPT4ByteFloat):
    """DPT 14.025 DPT_Value_Electric_FluxDensity."""

    unit = "C/m²"


class DPTElectricPolarization(DPT4ByteFloat):
    """DPT 14.026 DPT_Value_Electric_Polarization."""

    unit = "C/m²"


class DPTElectricPotential(DPT4ByteFloat):
    """DPT 14.027 DPT_Value_Electric_Potential."""

    unit = "V"


class DPTElectricPotentialDifference(DPT4ByteFloat):
    """DPT 14.028 DPT_Value_Electric_PotentialDifference."""

    unit = "V"


class DPTElectromagneticMoment(DPT4ByteFloat):
    """DPT 14.029 DPT_Value_ElectromagneticMoment."""

    unit = "A m²"


class DPTElectromotiveForce(DPT4ByteFloat):
    """DPT 14.030 DPT_Value_Electromotive_Force."""

    unit = "V"


class DPTEnergy(DPT4ByteFloat):
    """DPT 14.031 DPT_Value_Energy."""

    unit = 'J'


class DPTForce(DPT4ByteFloat):
    """DPT 14.032 DPT_Value_Force."""

    unit = "N"


class DPTFrequency(DPT4ByteFloat):
    """DPT 14.033 DPT_Value_Frequency."""

    unit = 'Hz'


class DPTAngularFrequency(DPT4ByteFloat):
    """DPT 14.034 DPT_Value_Angular_Frequency."""

    unit = "rad/s"


class DPTHeatCapacity(DPT4ByteFloat):
    """DPT 14.035 DPT_Value_Heat_Capacity."""

    unit = "J/K"


class DPTHeatFlowRate(DPT4ByteFloat):
    """DPT 14.036 DPT_Value_Heat_Flow_Rate."""

    unit = 'W'


class DPTHeatQuantity(DPT4ByteFloat):
    """DPT 14.037 DPT_Value_Heat_Quantity."""

    unit = "J"


class DPTImpedance(DPT4ByteFloat):
    """DPT 14.038 DPT_Value_Impedance."""

    unit = "Ω"


class DPTLength(DPT4ByteFloat):
    """DPT 14.039 DPT_Value_Length."""

    unit = "m"


class DPTLightQuantity(DPT4ByteFloat):
    """DPT 14.040 DPT_Value_Light_Quantity."""

    unit = "lm s"


class DPTLuminance(DPT4ByteFloat):
    """DPT 14.041 DPT_Value_Luminance."""

    unit = "cd/m²"
    ha_device_class = "illuminance"


class DPTLuminousFlux(DPT4ByteFloat):
    """DPT 14.042 DPT_Value_Heat_Flow_Rate."""

    unit = 'lm'
    ha_device_class = "illuminance"


class DPTLuminousIntensity(DPT4ByteFloat):
    """DPT 14.043 DPT_Value_Luminous_Intensity."""

    unit = "cd"
    ha_device_class = "illuminance"


class DPTMagneticFieldStrength(DPT4ByteFloat):
    """DPT 14.044 DPT_Value_Magnetic_FieldStrength."""

    unit = "A/m"


class DPTMagneticFlux(DPT4ByteFloat):
    """DPT 14.045 DPT_Value_Magnetic_Flux."""

    unit = "Wb"


class DPTMagneticFluxDensity(DPT4ByteFloat):
    """DPT 14.046 DPT_Value_Magnetic_FluxDensity."""

    unit = "T"


class DPTMagneticMoment(DPT4ByteFloat):
    """DPT 14.047 DPT_Value_Magnetic_Moment."""

    unit = "A m²"


class DPTMagneticPolarization(DPT4ByteFloat):
    """DPT 14.048 DPT_Value_Magnetic_Polarization."""

    unit = "T"


class DPTMagnetization(DPT4ByteFloat):
    """DPT 14.049 DPT_Value_Magnetization."""

    unit = "A/m"


class DPTMagnetomotiveForce(DPT4ByteFloat):
    """DPT 14.050 DPT_Value_MagnetomotiveForce."""

    unit = "A"


class DPTMass(DPT4ByteFloat):
    """DPT 14.051 DPT_Value_Mass."""

    unit = "kg"


class DPTMassFlux(DPT4ByteFloat):
    """DPT 14.052 DPT_Value_MassFlux."""

    unit = "kg/s"


class DPTMomentum(DPT4ByteFloat):
    """DPT 14.053 DPT_Value_Momentum."""

    unit = "N/s"


class DPTPhaseAngleRad(DPT4ByteFloat):
    """DPT 14.054 DPT_Value_Phase_Angle, Radiant."""

    unit = 'rad'


class DPTPhaseAngleDeg(DPT4ByteFloat):
    """DPT 14.055 DPT_Value_Phase_Angle, Degree."""

    unit = '°'


class DPTPower(DPT4ByteFloat):
    """DPT 14.056 DPT_Value_Power."""

    unit = "W"
    ha_device_class = "power"


class DPTPowerFactor(DPT4ByteFloat):
    """DPT 14.057 DPT_Value_Power."""

    unit = 'cosΦ'


class DPTPressure(DPT4ByteFloat):
    """DPT 14.058 DPT_Value_Pressure."""

    unit = 'Pa'
    ha_device_class = "pressure"


class DPTReactance(DPT4ByteFloat):
    """DPT 14.059 DPT_Value_Reactance."""

    unit = "Ω"


class DPTResistance(DPT4ByteFloat):
    """DPT 14.060 DPT_Value_Resistance."""

    unit = "Ω"


class DPTResistivity(DPT4ByteFloat):
    """DPT 14.061 DPT_Value_Resistivity."""

    unit = "Ω m"


class DPTSelfInductance(DPT4ByteFloat):
    """DPT 14.062 DPT_Value_SelfInductance."""

    unit = "H"


class DPTSolidAngle(DPT4ByteFloat):
    """DPT 14.063 DPT_Value_SolidAngle."""

    unit = "sr"


class DPTSoundIntensity(DPT4ByteFloat):
    """DPT 14.064 DPT_Value_Sound_Intensity."""

    unit = "W/m²"


class DPTSpeed(DPT4ByteFloat):
    """DPT 14.065 DPT_Value_Speed."""

    unit = 'm/s'


class DPTStress(DPT4ByteFloat):
    """DPT 14.066 DPT_Value_Stress."""

    unit = "Pa"


class DPTSurfaceTension(DPT4ByteFloat):
    """DPT 14.067 DPT_Value_Surface_Tension."""

    unit = "N/m"


class DPTCommonTemperature(DPT4ByteFloat):
    """DPT 14.068 DPT_Value_Common_Temperature."""

    unit = "°C"


class DPTAbsoluteTemperature(DPT4ByteFloat):
    """DPT 14.069 DPT_Value_Absolute_Temperature."""

    unit = "K"


class DPTTemperatureDifference(DPT4ByteFloat):
    """DPT 14.070 DPT_Value_TemperatureDifference."""

    unit = "K"


class DPTThermalCapacity(DPT4ByteFloat):
    """DPT 14.071 DPT_Value_Thermal_Capacity."""

    unit = "J/K"


class DPTThermalConductivity(DPT4ByteFloat):
    """DPT 14.072 DPT_Value_Thermal_Conductivity."""

    unit = "W/mK"


class DPTThermoelectricPower(DPT4ByteFloat):
    """DPT 14.073 DPT_Value_ThermoelectricPower."""

    unit = "V/K"


class DPTTimeSeconds(DPT4ByteFloat):
    """DPT 14.074 DPT_Value_Time."""

    unit = "s"


class DPTTorque(DPT4ByteFloat):
    """DPT 14.075 DPT_Value_Torque."""

    unit = "N m"


class DPTVolume(DPT4ByteFloat):
    """DPT 14.076 DPT_Value_Volume."""

    unit = "m³"


class DPTVolumeFlux(DPT4ByteFloat):
    """DPT 14.077 DPT_Value_Volume_Flux."""

    unit = "m³/s"


class DPTWeight(DPT4ByteFloat):
    """DPT 14.078 DPT_Value_Weight."""

    unit = "N"


class DPTWork(DPT4ByteFloat):
    """DPT 14.079 DPT_Value_Work."""

    unit = "J"
