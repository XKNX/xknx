"""
Module for managing a light via KNX.

It provides functionality for

* switching light 'on' and 'off'.
* setting the brightness.
* reading the current state from KNX bus.
"""
import asyncio

from xknx.exceptions import CouldNotParseTelegram
from xknx.knx import GroupAddress, DPTArray

from .device import Device
from .remote_value import RemoteValueSwitch1001


class Light(Device):
    """Class for managing a light."""

    def __init__(self,
                 xknx,
                 name,
                 group_address_switch=None,
                 group_address_switch_state=None,
                 group_address_brightness=None,
                 group_address_brightness_state=None,
                 device_updated_cb=None):
        """Initialize Light class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address_brightness, (str, int)):
            group_address_brightness = GroupAddress(group_address_brightness)
        if isinstance(group_address_brightness_state, (str, int)):
            group_address_brightness_state = GroupAddress(group_address_brightness_state)

        self.switch = RemoteValueSwitch1001(
            xknx,
            group_address_switch,
            group_address_switch_state,
            after_update_cb=self.after_update)

        self.group_address_brightness = group_address_brightness
        self.group_address_brightness_state = group_address_brightness_state

        self.brightness = 0
        self.supports_dimming = \
            group_address_brightness is not None

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_switch = \
            config.get('group_address_switch')
        group_address_switch_state = \
            config.get('group_address_switch_state')
        group_address_brightness = \
            config.get('group_address_brightness')
        group_address_brightness_state = \
            config.get('group_address_brightness_state')

        return cls(xknx,
                   name,
                   group_address_switch=group_address_switch,
                   group_address_switch_state=group_address_switch_state,
                   group_address_brightness=group_address_brightness,
                   group_address_brightness_state=group_address_brightness_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return (self.switch.has_group_address(group_address) or
                (self.group_address_brightness == group_address) or
                (self.group_address_brightness_state == group_address))

    def __str__(self):
        """Return object as readable string."""
        if not self.supports_dimming:
            return '<Light name="{0}" ' \
                    'switch="{1}" />' \
                    .format(
                        self.name,
                        self.switch.group_addr_str())

        return '<Light name="{0}" ' \
            'switch="{1}" ' \
            'group_address_brightness="{2}" ' \
            'group_address_brightness_state="{3}" ' \
            'brightness="{4}" />' \
            .format(
                self.name,
                self.switch.group_addr_str(),
                self.group_address_brightness,
                self.group_address_brightness_state,
                self.brightness)

    @property
    def state(self):
        """Return the current switch state of the device."""
        return self.switch.value == RemoteValueSwitch1001.Value.ON

    @asyncio.coroutine
    def _set_internal_brightness(self, brightness):
        """Set the internal brightness of the device. If state was changed after update hooks are executed."""
        if brightness != self.brightness:
            self.brightness = brightness
            yield from self.after_update()

    @asyncio.coroutine
    def set_on(self):
        """Switch light on."""
        yield from self.switch.on()

    @asyncio.coroutine
    def set_off(self):
        """Switch light off."""
        yield from self.switch.off()

    @asyncio.coroutine
    def set_brightness(self, brightness):
        """Set brightness of light."""
        if not self.supports_dimming:
            return
        yield from self.send(self.group_address_brightness, DPTArray(brightness))
        yield from self._set_internal_brightness(brightness)

    @asyncio.coroutine
    def do(self, action):
        """Execute 'do' commands."""
        if action == "on":
            yield from self.set_on()
        elif action == "off":
            yield from self.set_off()
        elif action.startswith("brightness:"):
            yield from self.set_brightness(int(action[11:]))
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.switch.state_addresses())
        if self.supports_dimming:
            state_address_brightness = \
                self.group_address_brightness_state or \
                self.group_address_brightness
            state_addresses.append(state_address_brightness)
        return state_addresses

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        yield from self.switch.process(telegram)

        if (self.supports_dimming and
                (telegram.group_address == self.group_address_brightness or
                 telegram.group_address == self.group_address_brightness_state)):
            yield from self._process_brightness(telegram)

    @asyncio.coroutine
    def _process_brightness(self, telegram):
        """Process incoming telegram for brightness state."""
        if not isinstance(telegram.payload, DPTArray) or \
                len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()

        yield from self._set_internal_brightness(telegram.payload.value[0])

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
