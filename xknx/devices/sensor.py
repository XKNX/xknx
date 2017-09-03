"""
Module for managing a sensor via KNX.

It provides functionality for

* reading the current state from KNX bus.
* watching for state updates from KNX bus.
"""
import asyncio
from xknx.knx import Address, DPTBinary, DPTArray, \
    DPTScaling, DPTTemperature, DPTLux, DPTWsp, DPTUElCurrentmA
from .device import Device


class Sensor(Device):
    """Class for managing a sensor."""

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 value_type=None,
                 device_class=None,
                 device_updated_cb=None):
        """Initialize Sensor class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if value_type == 'brightness':
            value_type = 'illuminance'
        self.group_address = group_address
        self.value_type = value_type
        self.device_class = device_class
        self.state = None

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')
        value_type = \
            config.get('value_type')
        device_class = \
            config.get('device_class')

        return cls(xknx,
                   name,
                   group_address=group_address,
                   value_type=value_type,
                   device_class=device_class)

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
        if self.value_type == 'percent':
            return "%"
        elif self.value_type == 'temperature':
            return "°C"
        elif self.value_type == 'illuminance':
            return "lx"
        elif self.value_type == 'speed_ms':
            return "m/s"
        elif self.value_type == 'current':
            return "mA"
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
        elif self.value_type == 'temperature':
            return DPTTemperature().from_knx(self.state.value)
        elif self.value_type == 'illuminance':
            return DPTLux().from_knx(self.state.value)
        elif self.value_type == 'speed_ms':
            return DPTWsp().from_knx(self.state.value)
        elif self.value_type == 'current':
            return DPTUElCurrentmA().from_knx(self.state.value)
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
