"""
Module for managing a sensor via KNX.

It provides functionality for

* reading the current state from KNX bus.
* watching for state updates from KNX bus.
"""
from .device import Device
from .remote_value_scaling import RemoteValueScaling
from .remote_value_sensor import RemoteValueSensor
from .remote_value_dpt_value_1_ucount import RemoteValueDptValue1Ucount


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
        super(Sensor, self).__init__(xknx, name, device_updated_cb)

        self.sensor_value = None
        if value_type == "percent":
            self.sensor_value = RemoteValueScaling(
                xknx,
                group_address_state=group_address,
                device_name=self.name,
                after_update_cb=self.after_update,
                range_from=0,
                range_to=100)
        elif value_type == "pulse":
            self.sensor_value = RemoteValueDptValue1Ucount(
                xknx,
                group_address=group_address,
                device_name=self.name,
                after_update_cb=self.after_update)
        else:
            self.sensor_value = RemoteValueSensor(
                xknx,
                group_address_state=group_address,
                device_name=self.name,
                after_update_cb=self.after_update,
                value_type=value_type)

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
        return self.sensor_value.has_group_address(group_address)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return self.sensor_value.state_addresses()

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self.sensor_value.process(telegram)

    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def resolve_state(self):
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    def __str__(self):
        """Return object as readable string."""
        return '<Sensor name="{0}" ' \
               'sensor="{1}" value="{2}" unit="{3}"/>' \
            .format(self.name,
                    self.sensor_value.group_addr_str(),
                    self.resolve_state(),
                    self.unit_of_measurement())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
