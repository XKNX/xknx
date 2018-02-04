"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
"""
from .device import Device
from .remote_value_switch import RemoteValueSwitch


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
        super(Switch, self).__init__(xknx, name, device_updated_cb)

        self.switch = RemoteValueSwitch(
            xknx,
            group_address,
            group_address_state,
            device_name=self.name,
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
        return self.switch.value == RemoteValueSwitch.Value.ON

    async def set_on(self):
        """Switch on switch."""
        await self.switch.on()

    async def set_off(self):
        """Switch off switch."""
        await self.switch.off()

    async def do(self, action):
        """Execute 'do' commands."""
        if action == "on":
            await self.set_on()
        elif action == "off":
            await self.set_off()
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return self.switch.state_addresses()

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self.switch.process(telegram)

    def __str__(self):
        """Return object as readable string."""
        return '<Switch name="{0}" switch="{1}" />' \
            .format(self.name,
                    self.switch.group_addr_str())

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
