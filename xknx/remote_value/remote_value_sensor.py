"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from xknx.dpt import (
    DPT2ByteFloat, DPT2ByteSigned, DPT2ByteUnsigned, DPT2Ucount, DPT4ByteFloat,
    DPT4ByteSigned, DPT4ByteUnsigned, DPTAngle, DPTArray, DPTBrightness,
    DPTColorTemperature, DPTDeltaTimeHrs, DPTDeltaTimeMin, DPTDeltaTimeMsec,
    DPTDeltaTimeSec, DPTElectricCurrent, DPTElectricPotential, DPTEnergy,
    DPTEnthalpy, DPTFrequency, DPTHeatFlowRate, DPTHumidity, DPTLuminousFlux,
    DPTLux, DPTPartsPerMillion, DPTPercentU8, DPTPercentV8, DPTPercentV16,
    DPTPhaseAngleDeg, DPTPhaseAngleRad, DPTPower, DPTPowerFactor, DPTPressure,
    DPTPressure2Byte, DPTRotationAngle, DPTScaling, DPTSceneNumber, DPTSpeed,
    DPTString, DPTTemperature, DPTUElCurrentmA, DPTValue1Count,
    DPTValue1Ucount, DPTValue2Count, DPTVoltage, DPTWsp)
from xknx.exceptions import ConversionError

from .remote_value import RemoteValue


class RemoteValueSensor(RemoteValue):
    """Abstraction for many different sensor DPT types."""

    DPTMAP = {
        'angle': DPTAngle,
        'brightness': DPTBrightness,
        'color_temperature': DPTColorTemperature,
        'counter_pulses': DPTValue1Count,
        'current': DPTUElCurrentmA,
        'delta_time_hrs': DPTDeltaTimeHrs,
        'delta_time_min': DPTDeltaTimeMin,
        'delta_time_ms': DPTDeltaTimeMsec,
        'delta_time_sec': DPTDeltaTimeSec,
        'electric_current': DPTElectricCurrent,
        'electric_potential': DPTElectricPotential,
        'energy': DPTEnergy,
        'enthalpy': DPTEnthalpy,
        'frequency': DPTFrequency,
        'heatflowrate': DPTHeatFlowRate,
        'humidity': DPTHumidity,
        'illuminance': DPTLux,
        'luminous_flux': DPTLuminousFlux,
        'percent': DPTScaling,
        'percentU8': DPTPercentU8,
        'percentV8': DPTPercentV8,
        'percentV16': DPTPercentV16,
        'phaseanglerad': DPTPhaseAngleRad,
        'phaseangledeg': DPTPhaseAngleDeg,
        'power': DPTPower,
        'powerfactor': DPTPowerFactor,
        'ppm': DPTPartsPerMillion,
        'pressure': DPTPressure,
        'pressure_2byte': DPTPressure2Byte,
        'pulse': DPTValue1Ucount,
        'rotation_angle': DPTRotationAngle,
        'scene_number': DPTSceneNumber,
        'speed': DPTSpeed,
        'speed_ms': DPTWsp,
        'string': DPTString,
        'temperature': DPTTemperature,
        'voltage': DPTVoltage,
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
