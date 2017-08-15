"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
"""
import asyncio
from xknx.knx import Address, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from .device import Device


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

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if isinstance(group_address_state, (str, int)):
            group_address_state = Address(group_address_state)

        self.group_address = group_address
        self.group_address_state = group_address_state
        self.state = False

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
        return (self.group_address == group_address) or \
               (self.group_address_state == group_address)

    @asyncio.coroutine
    def _set_internal_state(self, state):
        """Set the internal state of the device. If state was changed after update hooks are executed."""
        if state != self.state:
            self.state = state
            yield from self.after_update()

    @asyncio.coroutine
    def set_on(self):
        """Switch on switch."""
        yield from self.send(self.group_address, DPTBinary(1))
        yield from self._set_internal_state(True)

    @asyncio.coroutine
    def set_off(self):
        """Switch off switch."""
        yield from self.send(self.group_address, DPTBinary(0))
        yield from self._set_internal_state(False)

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
        return [self.group_address_state or self.group_address, ]

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        if not isinstance(telegram.payload, DPTBinary):
            raise CouldNotParseTelegram()

        if telegram.payload.value == 0:
            yield from self._set_internal_state(False)
        elif telegram.payload.value == 1:
            yield from self._set_internal_state(True)
        else:
            raise CouldNotParseTelegram()

    def __str__(self):
        """Return object as readable string."""
        return '<Switch name="{0}" group_address="{1}" ' \
               'group_address_state="{2}" state="{3}" />' \
            .format(self.name,
                    self.group_address,
                    self.group_address_state,
                    self.state)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
