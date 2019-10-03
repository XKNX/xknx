"""
Module for managing a fan via KNX.

It provides functionality for

* setting fan to specific speed
* reading the current speed from KNX bus.
"""
from xknx.remote_value import RemoteValueScaling

from .device import Device


class Fan(Device):
    """Class for managing a fan."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(self,
                 xknx,
                 name,
                 group_address_speed=None,
                 group_address_speed_state=None,
                 device_updated_cb=None):
        """Initialize fan class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)

        self.speed = RemoteValueScaling(
            xknx,
            group_address_speed,
            group_address_speed_state,
            device_name=self.name,
            after_update_cb=self.after_update,
            range_from=0,
            range_to=100)

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_speed = \
            config.get('group_address_speed')
        group_address_speed_state = \
            config.get('group_address_speed_state')

        return cls(
            xknx,
            name,
            group_address_speed=group_address_speed,
            group_address_speed_state=group_address_speed_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.speed.has_group_address(group_address)

    def __str__(self):
        """Return object as readable string."""
        return '<Fan name="{0}" ' \
            'speed="{1}" />' \
            .format(
                self.name,
                self.speed.group_addr_str())

    async def set_speed(self, speed):
        """Set the fan to a desginated speed."""
        await self.speed.set(speed)

    async def do(self, action):
        """Execute 'do' commands."""
        if action.startswith("speed:"):
            await self.set_speed(int(action[6:]))
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.speed.state_addresses())
        return state_addresses

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self.speed.process(telegram)

    @property
    def current_speed(self):
        """Return current speed of fan."""
        return self.speed.value

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
