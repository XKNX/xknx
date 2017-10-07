"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
"""
import asyncio
from .device import Device
from .remote_value import RemoteValueSwitch1001


class Switch(Device):
    """Class for managing a switch."""

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 group_address_state=None,
                 device_updated_cb=None):
        """Initialize Switch class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)

        self.switch = RemoteValueSwitch1001(
            xknx,
            group_address,
            group_address_state,
            after_update_cb=self.after_update)

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')
        group_address_state = \
            config.get('group_address_state')

        return cls(xknx,
                   name,
                   group_address=group_address,
                   group_address_state=group_address_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.switch.has_group_address(group_address)

    @property
    def state(self):
        """Return the current switch state of the device."""
        return self.switch.value == RemoteValueSwitch1001.Value.ON

    @asyncio.coroutine
    def set_on(self):
        """Switch on switch."""
        yield from self.switch.on()

    @asyncio.coroutine
    def set_off(self):
        """Switch off switch."""
        yield from self.switch.off()

    @asyncio.coroutine
    def do(self, action):
        """Execute 'do' commands."""
        if action == "on":
            yield from self.set_on()
        elif action == "off":
            yield from self.set_off()
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return self.switch.state_addresses()

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        yield from self.switch.process(telegram)

    def __str__(self):
        """Return object as readable string."""
        return '<Switch name="{0}" switch="{1}" />' \
            .format(self.name,
                    self.switch.group_addr_str())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
