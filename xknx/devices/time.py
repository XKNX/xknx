"""
Module for broadcasting time to KNX bus.

Time is a virtual/pseudo device, using the infrastructure for
beeing configured via xknx.yaml and synchronized periodically
by StateUpdate.
"""

import asyncio
from xknx.knx import Address, DPTArray, DPTTime
from .device import Device


class Time(Device):
    """Class for virtual time device."""

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 device_updated_cb=None):
        """Initialize Time class."""
        Device.__init__(self, xknx, name, device_updated_cb)

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)

        self.group_address = group_address

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')
        return cls(xknx,
                   name,
                   group_address=group_address)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.group_address == group_address

    @asyncio.coroutine
    def broadcast_time(self):
        """Broadcast time to KNX bus."""
        yield from self.send(
            self.group_address,
            DPTArray(DPTTime.current_time_as_knx()))

    @asyncio.coroutine
    def sync(self, wait_for_result=True):
        """Read state of device from KNX bus. Used here to broadcast time to KNX bus."""
        yield from self.broadcast_time()

    def __str__(self):
        """Return object as readable string."""
        return '<Time name="{0}" group_address="{1}" />' \
            .format(self.name, self.group_address)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
