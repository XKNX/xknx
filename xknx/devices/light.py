"""
Module for managing a light via KNX.

It provides functionality for

* switching light 'on' and 'off'.
* setting the brightness.
* reading the current state from KNX bus.
"""
from .device import Device
from .remote_value_color_rgb import RemoteValueColorRGB
from .remote_value_switch import RemoteValueSwitch
from .remote_value_scaling import RemoteValueScaling


class Light(Device):
    """Class for managing a light."""

    def __init__(self,
                 xknx,
                 name,
                 group_address_switch=None,
                 group_address_switch_state=None,
                 group_address_brightness=None,
                 group_address_brightness_state=None,
                 group_address_color=None,
                 group_address_color_state=None,
                 device_updated_cb=None):
        """Initialize Light class."""
        # pylint: disable=too-many-arguments
        super(Light, self).__init__(xknx, name, device_updated_cb)

        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            device_name=self.name,
            after_update_cb=self.after_update)

        self.brightness = RemoteValueScaling(
            xknx,
            group_address_brightness,
            group_address_brightness_state,
            device_name=self.name,
            after_update_cb=self.after_update,
            range_from=0,
            range_to=255)

        self.color = RemoteValueColorRGB(
            xknx,
            group_address_color,
            group_address_color_state,
            device_name=self.name,
            after_update_cb=self.after_update)

    @property
    def supports_brightness(self):
        """Return if cover supports direct positioning."""
        return self.brightness.initialized

    @property
    def supports_color(self):
        """Return if cover supports direct positioning."""
        return self.color.initialized

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
        group_address_color = \
            config.get('group_address_color')
        group_address_color_state = \
            config.get('group_address_color_state')

        return cls(xknx,
                   name,
                   group_address_switch=group_address_switch,
                   group_address_switch_state=group_address_switch_state,
                   group_address_brightness=group_address_brightness,
                   group_address_brightness_state=group_address_brightness_state,
                   group_address_color=group_address_color,
                   group_address_color_state=group_address_color_state)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return (self.switch.has_group_address(group_address) or
                self.brightness.has_group_address(group_address) or
                self.color.has_group_address(group_address))

    def __str__(self):
        """Return object as readable string."""
        str_brightness = '' if not self.supports_brightness else \
            ' brightness="{0}"'.format(
                self.brightness.group_addr_str())

        str_color = '' if not self.supports_color else \
            ' color="{0}"'.format(
                self.color.group_addr_str())

        return '<Light name="{0}" ' \
            'switch="{1}"{2}{3} />' \
            .format(
                self.name,
                self.switch.group_addr_str(),
                str_brightness,
                str_color)

    @property
    def state(self):
        """Return the current switch state of the device."""
        return self.switch.value == RemoteValueSwitch.Value.ON

    async def set_on(self):
        """Switch light on."""
        await self.switch.on()

    async def set_off(self):
        """Switch light off."""
        await self.switch.off()

    @property
    def current_brightness(self):
        """Return current color of light."""
        return self.brightness.value

    async def set_brightness(self, brightness):
        """Set brightness of light."""
        if not self.supports_brightness:
            self.xknx.logger.warning("Dimming not supported for device %s", self.get_name())
            return
        await self.brightness.set(brightness)

    async def set_color(self, color):
        """Set color of light."""
        if not self.supports_color:
            self.xknx.logger.warning("Colors not supported for device %s", self.get_name())
            return
        await self.color.set(color)

    @property
    def current_color(self):
        """Return current color of light."""
        return self.color.value

    async def do(self, action):
        """Execute 'do' commands."""
        if action == "on":
            await self.set_on()
        elif action == "off":
            await self.set_off()
        elif action.startswith("brightness:"):
            await self.set_brightness(int(action[11:]))
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        state_addresses.extend(self.switch.state_addresses())
        state_addresses.extend(self.color.state_addresses())
        state_addresses.extend(self.brightness.state_addresses())
        return state_addresses

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        await self.switch.process(telegram)
        await self.color.process(telegram)
        await self.brightness.process(telegram)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
