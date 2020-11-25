"""
Module for managing a light via KNX using individual group addresses for red, green, blue and white.

It provides functionality for

* switching light 'on' and 'off'.
* setting the color using individual group addresses for red, green, blue and white.
* reading the current state from the KNX bus.
"""
import logging
from typing import Optional

from xknx.remote_value import RemoteValueScaling, RemoteValueSwitch

from .device import Device

logger = logging.getLogger("xknx.log")


class _SwitchAndBrightness:
    def __init__(
        self,
        xknx,
        name,
        feature_name: str,
        group_address_switch=None,
        group_address_switch_state=None,
        group_address_brightness=None,
        group_address_brightness_state=None,
        after_update_cb=None,
    ):
        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            device_name=name,
            feature_name=feature_name + "_state",
            after_update_cb=after_update_cb,
        )
        self.brightness = RemoteValueScaling(
            xknx,
            group_address_brightness,
            group_address_brightness_state,
            device_name=name,
            feature_name=feature_name + "_brightness",
            after_update_cb=after_update_cb,
            range_from=0,
            range_to=255,
        )

    @property
    def is_on(self):
        """Return if light supports color."""
        return self.switch.value

    async def set_on(self):
        """Switch light on."""
        if self.switch.initialized:
            await self.switch.on()

    async def set_off(self):
        """Switch light off."""
        if self.switch.initialized:
            await self.switch.off()

    def __eq__(self, other):
        """Compare for quality."""
        return self.__dict__ == other.__dict__


# pylint: disable=too-many-public-methods, too-many-instance-attributes
class RGBLight(Device):
    """Class for managing a light."""

    def __init__(
        self,
        xknx,
        name,
        group_address_switch_red=None,
        group_address_switch_state_red=None,
        group_address_brightness_red=None,
        group_address_brightness_state_red=None,
        group_address_switch_green=None,
        group_address_switch_state_green=None,
        group_address_brightness_green=None,
        group_address_brightness_state_green=None,
        group_address_switch_blue=None,
        group_address_switch_state_blue=None,
        group_address_brightness_blue=None,
        group_address_brightness_state_blue=None,
        group_address_switch_white=None,
        group_address_switch_state_white=None,
        group_address_brightness_white=None,
        group_address_brightness_state_white=None,
        device_updated_cb=None,
    ):
        """Initialize Light class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.red = _SwitchAndBrightness(
            xknx,
            self.name,
            "red",
            group_address_switch_red,
            group_address_switch_state_red,
            group_address_brightness_red,
            group_address_brightness_state_red,
            self.after_update,
        )

        self.green = _SwitchAndBrightness(
            xknx,
            self.name,
            "green",
            group_address_switch_green,
            group_address_switch_state_green,
            group_address_brightness_green,
            group_address_brightness_state_green,
            self.after_update,
        )

        self.blue = _SwitchAndBrightness(
            xknx,
            self.name,
            "blue",
            group_address_switch_blue,
            group_address_switch_state_blue,
            group_address_brightness_blue,
            group_address_brightness_state_blue,
            self.after_update,
        )

        self.white = _SwitchAndBrightness(
            xknx,
            self.name,
            "white",
            group_address_switch_white,
            group_address_switch_state_white,
            group_address_brightness_white,
            group_address_brightness_state_white,
            self.after_update,
        )

    def _iter_colors(self):
        """Iterate the devices RemoteValue classes."""
        if self.white.brightness.initialized:
            yield from (
                self.red,
                self.green,
                self.blue,
                self.white,
            )
        else:
            yield from (
                self.red,
                self.green,
                self.blue,
                # self.white,
            )

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        for remote_value in self._iter_colors():
            yield remote_value.switch
            yield remote_value.brightness

    @property
    def supports_brightness(self):
        """Return if light supports brightness."""
        return False

    @property
    def supports_color(self):
        """Return if light supports color."""
        return self.green.brightness.initialized and self.blue.brightness.initialized

    @property
    def supports_rgbw(self):
        """Return if light supports RGBW."""
        return self.supports_color and self.white.brightness.initialized

    @property
    def supports_tunable_white(self):
        """Return if light supports tunable white / relative color temperature."""
        return False

    @property
    def supports_color_temperature(self):
        """Return if light supports absolute color temperature."""
        return False

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_switch_red = config.get("group_address_switch_red")
        group_address_switch_state_red = config.get("group_address_switch_state_red")
        group_address_brightness_red = config.get("group_address_brightness_red")
        group_address_brightness_state_red = config.get(
            "group_address_brightness_state_red"
        )

        group_address_switch_green = config.get("group_address_switch_green")
        group_address_switch_state_green = config.get(
            "group_address_switch_state_green"
        )
        group_address_brightness_green = config.get("group_address_brightness_green")
        group_address_brightness_state_green = config.get(
            "group_address_brightness_state_green"
        )

        group_address_switch_blue = config.get("group_address_switch_blue")
        group_address_switch_state_blue = config.get("group_address_switch_state_blue")
        group_address_brightness_blue = config.get("group_address_brightness_blue")
        group_address_brightness_state_blue = config.get(
            "group_address_brightness_state_blue"
        )

        group_address_switch_white = config.get("group_address_switch")
        group_address_switch_state_white = config.get("group_address_switch_state")
        group_address_brightness_white = config.get("group_address_brightness")
        group_address_brightness_state_white = config.get(
            "group_address_brightness_state"
        )

        return cls(
            xknx,
            name,
            group_address_switch_red=group_address_switch_red,
            group_address_switch_state_red=group_address_switch_state_red,
            group_address_brightness_red=group_address_brightness_red,
            group_address_brightness_state_red=group_address_brightness_state_red,
            group_address_switch_green=group_address_switch_green,
            group_address_switch_state_green=group_address_switch_state_green,
            group_address_brightness_green=group_address_brightness_green,
            group_address_brightness_state_green=group_address_brightness_state_green,
            group_address_switch_blue=group_address_switch_blue,
            group_address_switch_state_blue=group_address_switch_state_blue,
            group_address_brightness_blue=group_address_brightness_blue,
            group_address_brightness_state_blue=group_address_brightness_state_blue,
            group_address_switch_white=group_address_switch_white,
            group_address_switch_state_white=group_address_switch_state_white,
            group_address_brightness_white=group_address_brightness_white,
            group_address_brightness_state_white=group_address_brightness_state_white,
        )

    def __str__(self):
        """Return object as readable string."""
        str_red_state = (
            ""
            if not self.red.switch.initialized
            else f' red_state="{self.red.switch.group_addr_str()}"'
        )
        str_red_brightness = (
            ""
            if not self.red.brightness.initialized
            else f' red_brightness="{self.red.brightness.group_addr_str()}"'
        )

        str_green_state = (
            ""
            if not self.green.switch.initialized
            else f' green_state="{self.green.switch.group_addr_str()}"'
        )
        str_green_brightness = (
            ""
            if not self.green.brightness.initialized
            else f' green_brightness="{self.green.brightness.group_addr_str()}"'
        )

        str_blue_state = (
            ""
            if not self.blue.switch.initialized
            else f' blue_state="{self.blue.switch.group_addr_str()}"'
        )
        str_blue_brightness = (
            ""
            if not self.blue.brightness.initialized
            else f' blue_brightness="{self.blue.brightness.group_addr_str()}"'
        )

        str_white_state = (
            ""
            if not self.white.switch.initialized
            else f' white_state="{self.white.switch.group_addr_str()}"'
        )
        str_white_brightness = (
            ""
            if not self.white.brightness.initialized
            else f' white_brightness="{self.white.brightness.group_addr_str()}"'
        )

        return '<Light name="{}" {}{}{}{}{}{}{}{} />'.format(
            self.name,
            str_red_state,
            str_red_brightness,
            str_green_state,
            str_green_brightness,
            str_blue_state,
            str_blue_brightness,
            str_white_state,
            str_white_brightness,
        )

    @property
    def state(self) -> Optional[bool]:
        """Return the current switch state of the device."""
        res = False
        for color in self._iter_colors():
            res = res or bool(color.is_on)
        return res

    async def set_on(self):
        """Switch light on."""
        for color in self._iter_colors():
            await color.set_on()

    async def set_off(self):
        """Switch light off."""
        for color in self._iter_colors():
            await color.set_off()

    @property
    def current_color(self):
        """
        Return current color of light.

        If the device supports RGBW, get the current RGB+White values instead.
        """
        colors = [
            self.red.brightness.value,
            self.green.brightness.value,
            self.blue.brightness.value,
        ]
        if None in colors:
            return None, self.white.brightness.value
        return colors, self.white.brightness.value

    async def set_color(self, color, white=None):
        """
        Set color of a light device.

        If also the white value is given and the device supports RGBW,
        set all four values.
        """
        if white is not None:
            if not self.supports_rgbw:
                logger.warning("RGBW not supported for device %s", self.get_name())
                return
            await self.red.brightness.set(color[0])
            await self.green.brightness.set(color[1])
            await self.blue.brightness.set(color[2])
            await self.white.brightness.set(white)
        else:
            if not self.supports_color:
                logger.warning("Colors not supported for device %s", self.get_name())
                return
            await self.red.brightness.set(color[0])
            await self.green.brightness.set(color[1])
            await self.blue.brightness.set(color[2])

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
        for remote_value in self._iter_remote_values():
            await remote_value.process(telegram)
