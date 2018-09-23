"""
Module for managing a remote value typically used within a sensor.

The module maps a given value_type to a DPT class and uses this class
for serialization and deserialization of the KNX value.
"""
from xknx.exceptions import ConversionError
from xknx.knx import (DPT2ByteFloat, DPT2ByteUnsigned, DPT4ByteFloat,
                      DPT4ByteSigned, DPT4ByteUnsigned, DPTArray,
                      DPTBrightness, DPTElectricCurrent, DPTElectricPotential,
                      DPTEnergy, DPTFrequency, DPTHeatFlowRate, DPTHumidity,
                      DPTLux, DPTPhaseAngleDeg, DPTPhaseAngleRad, DPTPower,
                      DPTPowerFactor, DPTSpeed, DPTTemperature, DPTEnthalpy,
                      DPTUElCurrentmA, DPTWsp, DPTPartsPerMillion, DPTVoltage)

from .remote_value import RemoteValue


class RemoteValueSensor(RemoteValue):
    """Abstraction for many different sensor DPT types."""

    DPTMAP = {
        'temperature': DPTTemperature,
        'humidity': DPTHumidity,
        'illuminance': DPTLux,
        'brightness': DPTBrightness,
        'speed_ms': DPTWsp,
        'current': DPTUElCurrentmA,
        'voltage': DPTVoltage,
        'power': DPTPower,
        'electric_current': DPTElectricCurrent,
        'electric_potential': DPTElectricPotential,
        'energy': DPTEnergy,
        'frequency': DPTFrequency,
        'heatflowrate': DPTHeatFlowRate,
        'phaseanglerad': DPTPhaseAngleRad,
        'phaseangledeg': DPTPhaseAngleDeg,
        'powerfactor': DPTPowerFactor,
        'speed': DPTSpeed,
        'enthalpy': DPTEnthalpy,
        'ppm': DPTPartsPerMillion,

        #  Generic DPT Without Min/Max and Unit.
        'DPT-7': DPT2ByteUnsigned,
        '2byte_unsigned': DPT2ByteUnsigned,
        'DPT-9': DPT2ByteFloat,

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
                 value_type=None,
                 device_name=None,
                 after_update_cb=None):
        """Initialize RemoteValueSensor class."""
        # pylint: disable=too-many-arguments
        super(RemoteValueSensor, self).__init__(
            xknx, group_address, group_address_state,
            device_name=device_name, after_update_cb=after_update_cb)
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
