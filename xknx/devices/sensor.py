"""
Module for managing a sensor via KNX.

It provides functionality for

* reading the current state from KNX bus.
* watching for state updates from KNX bus.
"""
import asyncio

from xknx.knx import (GroupAddress, DPTArray, DPTBinary, DPTHumidity, DPTLux,
                      DPTScaling, DPTTemperature, DPTElectricPotential,
                      DPTElectricCurrent, DPTPower, DPTUElCurrentmA, DPTWsp,
                      DPTBrightness, DPTEnergy, DPTHeatFlowRate, DPTFrequency, DPTPhaseAngleRad, DPTPhaseAngleDeg,
                      DPTPowerFactor, DPTSpeed,
                      DPT2ByteUnsigned, DPT2ByteFloat, DPT4ByteUnsigned, DPT4ByteSigned, DPT4ByteFloat)

from .device import Device


class Sensor(Device):
    """Class for managing a sensor."""

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 value_type=None,
                 device_updated_cb=None):
        """Initialize Sensor class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address, (str, int)):
            group_address = GroupAddress(group_address)
        if value_type == 'brightness':
            value_type = 'illuminance'
        self.group_address = group_address
        self.value_type = value_type
        self.state = None

        self.dptmap = {
            'temperature'       : DPTTemperature,
            'humidity'          : DPTHumidity,
            'illuminance'       : DPTLux,
            'brightness'        : DPTBrightness,
            'speed_ms'          : DPTWsp,
            'current'           : DPTUElCurrentmA,
            'power'             : DPTPower,
            'electric_current'  : DPTElectricCurrent,
            'electric_potential': DPTElectricPotential,
            'energy'            : DPTEnergy,
            'frequency'         : DPTFrequency,
            'heatflowrate'      : DPTHeatFlowRate,
            'phaseanglerad'     : DPTPhaseAngleRad,
            'phaseangledeg'     : DPTPhaseAngleDeg,
            'powerfactor'       : DPTPowerFactor,
            'speed'             : DPTSpeed,

            # Generic DPT Without Min/Max and Unit.
            'DPT-7'             : DPT2ByteUnsigned,
            '2byte_unsigned'    : DPT2ByteUnsigned,
            'DPT-9'             : DPT2ByteFloat,

            'DPT-12'            : DPT4ByteUnsigned,
            '4byte_unsigned'    : DPT4ByteUnsigned,

            'DPT-13'            : DPT4ByteSigned,
            '4byte_signed'      : DPT4ByteSigned,
            'DPT-14'            : DPT4ByteFloat,
            '4byte_float'       : DPT4ByteFloat
        }

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')
        value_type = \
            config.get('value_type')

        return cls(xknx,
                   name,
                   group_address=group_address,
                   value_type=value_type)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.group_address == group_address

    @asyncio.coroutine
    def _set_internal_state(self, state):
        """Set the internal state of the device. If state was changed after update hooks are executed."""
        if state != self.state:
            self.state = state
            yield from self.after_update()

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return [self.group_address, ]

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        yield from self._set_internal_state(telegram.payload)

    def unit_of_measurement(self):
        """Return the unit of measurement."""
        # pylint: disable=too-many-return-statements
        if self.value_type == 'percent':
            return "%"
        elif self.value_type in self.dptmap:
            return self.dptmap[self.value_type].unit
        return None

    def resolve_state(self):
        """Return the current state of the sensor as a human readable string."""
        # pylint: disable=invalid-name,too-many-return-statements
        if self.state is None:
            return None
        elif self.value_type == 'percent' and \
                isinstance(self.state, DPTArray) and \
                len(self.state.value) == 1:
            # TODO: Instanciate DPTScaling object with DPTArray class
            return "{0}".format(DPTScaling().from_knx(self.state.value))
        elif self.value_type in self.dptmap:
            return self.dptmap[self.value_type].from_knx(self.state.value)
        elif isinstance(self.state, DPTArray):
            return ','.join('0x%02x' % i for i in self.state.value)
        elif isinstance(self.state, DPTBinary):
            return "{0:b}".format(self.state.value)
        raise TypeError()

    def __str__(self):
        """Return object as readable string."""
        return '<Sensor name="{0}" ' \
               'group_address="{1}" ' \
               'state="{2}" ' \
               'resolve_state="{3}" />' \
            .format(self.name,
                    self.group_address,
                    self.state,
                    self.resolve_state())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
