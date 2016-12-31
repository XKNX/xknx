import logging

#import homeassistant.components.xknx as xknx_component
import custom_components.xknx as xknx_component

import xknx

from homeassistant.components.light import ( ATTR_BRIGHTNESS, SUPPORT_BRIGHTNESS, Light )


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the demo light platform."""

    if xknx_component.xknx_wrapper is None or not xknx_component.xknx_wrapper.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    lights = []

    for device in xknx_component.xknx_wrapper.xknx.devices.devices:
        if isinstance(device, xknx.Light):
            lights.append(XKNX_Light(hass, device))

    add_devices_callback(lights)

    return True    


class XKNX_Light(Light):
    """Representation of XKNX lights."""

    def __init__(self, hass, device):
        self.device = device
        self.register_callbacks()

    def register_callbacks(self):
        def after_update_callback(device):
            self.update()
        self.device.after_update_callback = after_update_callback

    def update(self):
        self.update_ha_state()

    @property
    def should_poll(self):
        """No polling needed for a demo light."""
        return False

    @property
    def name(self):
        """Return the name of the light if any."""
        return self.device.name

    @property
    def brightness(self):
        """Return the brightness of this light between 0..255."""
        return self.device.brightness

    @property
    def xy_color(self):
        """Return the XY color value [float, float]."""
        return None;

    @property
    def rgb_color(self):
        """Return the RBG color value."""
        return None

    @property
    def color_temp(self):
        """Return the CT color temperature."""
        return None

    @property
    def white_value(self):
        """Return the white value of this light between 0..255."""
        return None

    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return None

    @property
    def effect(self):
        """Return the current effect."""
        return None

    @property
    def is_on(self):
        """Return true if light is on."""
        return self.device.state

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    def turn_on(self, **kwargs):
        """Turn the light on."""
        if ATTR_BRIGHTNESS in kwargs:
            self.device.set_brightness(int(kwargs[ATTR_BRIGHTNESS]))
        else:
            self.device.set_on()
        self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        """Turn the light off."""
        self.device.set_off()
        self.schedule_update_ha_state()
