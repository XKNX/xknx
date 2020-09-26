"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
"""
import logging

from xknx.remote_value import RemoteValueSwitch

from .device import Device

logger = logging.getLogger("xknx.log")


class Switch(Device):
    """Class for managing a switch."""

    def __init__(
        self,
        xknx,
        name,
        group_address=None,
        group_address_state=None,
        device_updated_cb=None,
    ):
        """Initialize Switch class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.switch = RemoteValueSwitch(
            xknx,
            group_address,
            group_address_state,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        yield self.switch

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        group_address_state = config.get("group_address_state")

        return cls(
            xknx,
            name,
            group_address=group_address,
            group_address_state=group_address_state,
        )

    @property
    def state(self):
        """Return the current switch state of the device."""
        # None will return False
        return bool(self.switch.value)

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
            logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )

    async def process_group_write(self, telegram):
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.switch.process(telegram)

    def __str__(self):
        """Return object as readable string."""
        return '<Switch name="{}" switch="{}" />'.format(
            self.name, self.switch.group_addr_str()
        )
