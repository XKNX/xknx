"""
Module for managing a light via KNX.

It provides functionality for

* switching light 'on' and 'off'.
* setting the brightness.
* reading the current state from KNX bus.
"""
import asyncio
from xknx.knx import Address, DPTBinary, DPTArray
from xknx.exceptions import CouldNotParseTelegram
from .device import Device


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
        if isinstance(group_address_switch, (str, int)):
            group_address_switch = Address(group_address_switch)
        if isinstance(group_address_switch_state, (str, int)):
            group_address_switch_state = Address(group_address_switch_state)
        if isinstance(group_address_brightness, (str, int)):
            group_address_brightness = Address(group_address_brightness)
        if isinstance(group_address_brightness_state, (str, int)):
            group_address_brightness_state = Address(group_address_brightness_state)

        self.group_address_switch = group_address_switch
        self.group_address_switch_state = group_address_switch_state
        self.group_address_brightness = group_address_brightness
        self.group_address_brightness_state = group_address_brightness_state
        self.state = False
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
        return (self.group_address_switch == group_address) or \
               (self.group_address_switch_state == group_address) or \
               (self.group_address_brightness == group_address) or \
               (self.group_address_brightness_state == group_address)

    def __str__(self):
        """Return object as readable string."""
        if not self.supports_dimming:
            return '<Light name="{0}" ' \
                    'group_address_switch="{1}" ' \
                    'group_address_switch_state="{2}" ' \
                    'state="{3}" />' \
                    .format(
                        self.name,
                        self.group_address_switch,
                        self.group_address_switch_state,
                        self.state)

        return '<Light name="{0}" ' \
            'group_address_switch="{1}" ' \
            'group_address_switch_state="{2}" ' \
            'group_address_brightness="{3}" ' \
            'group_address_brightness_state="{4}" ' \
            'state="{5}" brightness="{6}" />' \
            .format(
                self.name,
                self.group_address_switch,
                self.group_address_switch_state,
                self.group_address_brightness,
                self.group_address_brightness_state,
                self.state,
                self.brightness)

    @asyncio.coroutine
    def _set_internal_state(self, state):
        """Set the internal state of the device. If state was changed after update hooks are executed."""
        if state != self.state:
            self.state = state
            yield from self.after_update()

    @asyncio.coroutine
    def _set_internal_brightness(self, brightness):
        """Set the internal brightness of the device. If state was changed after update hooks are executed."""
        if brightness != self.brightness:
            self.brightness = brightness
            yield from self.after_update()

    @asyncio.coroutine
    def set_on(self):
        """Switch light on."""
        yield from self.send(self.group_address_switch, DPTBinary(1))
        yield from self._set_internal_state(True)

    @asyncio.coroutine
    def set_off(self):
        """Switch light off."""
        yield from self.send(self.group_address_switch, DPTBinary(0))
        yield from self._set_internal_state(False)

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
        state_address_switch = \
            self.group_address_switch_state or \
            self.group_address_switch
        state_addresses = [state_address_switch]
        if self.supports_dimming:
            state_address_brightness = \
                self.group_address_brightness_state or \
                self.group_address_brightness
            state_addresses.append(state_address_brightness)
        return state_addresses

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        if telegram.group_address == self.group_address_switch or \
                telegram.group_address == self.group_address_switch_state:
            yield from self._process_state(telegram)
        elif (self.supports_dimming and
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

    @asyncio.coroutine
    def _process_state(self, telegram):
        """Process incoming telegram for on/off state."""
        if not isinstance(telegram.payload, DPTBinary):
            raise CouldNotParseTelegram()
        if telegram.payload.value == 0:
            yield from self._set_internal_state(False)
        elif telegram.payload.value == 1:
            yield from self._set_internal_state(True)
        else:
            raise CouldNotParseTelegram()

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
