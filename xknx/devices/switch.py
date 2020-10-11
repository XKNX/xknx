"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
"""
import asyncio
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
        reset_after=None,
        group_address=None,
        group_address_state=None,
        device_updated_cb=None,
    ):
        """Initialize Switch class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.reset_after = reset_after
        self._reset_task = None
        self.state = False

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

    def __del__(self):
        """Destructor. Cleaning up if this was not done before."""
        if self._reset_task:
            self._reset_task.cancel()

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
        if await self.switch.process(telegram):
            self.state = self.switch.value
            if self.reset_after is not None and self.state:
                if self._reset_task:
                    self._reset_task.cancel()
                self._reset_task = asyncio.create_task(
                    self._reset_state(self.reset_after)
                )

    async def _reset_state(self, wait_seconds: float):
        await asyncio.sleep(wait_seconds)
        await self.set_off()

    def __str__(self):
        """Return object as readable string."""
        return '<Switch name="{}" switch="{}" />'.format(
            self.name, self.switch.group_addr_str()
        )
