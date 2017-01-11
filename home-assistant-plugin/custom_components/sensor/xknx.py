import logging

#import homeassistant.components.xknx as xknx_component
import custom_components.xknx as xknx_component

import xknx

from homeassistant.helpers.entity import Entity

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the demo light platform."""

    if xknx_component.xknx_wrapper is None or not xknx_component.xknx_wrapper.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    lights = []

    for device in xknx_component.xknx_wrapper.xknx.devices.devices:
        if isinstance(device, xknx.Sensor):
            lights.append(XKNX_Sensor(hass, device))

    add_devices_callback(lights)

    return True


class XKNX_Sensor(Entity):

    def __init__(self, hass, device):
        self.device = device
        self.register_callbacks()

    @property
    def should_poll(self):
        """No polling needed for a demo sensor."""
        return False


    def register_callbacks(self):
        def after_update_callback(device):
            self.update()
        self.device.after_update_callback = after_update_callback


    def update(self):
        self.update_ha_state()


    @property
    def name(self):
        """Return the name of the light if any."""
        return self.device.name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.device.state_str()

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self.device.unit_of_measurement()

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        #return {
        #    "FNORD": "FNORD",
        #}
        return None
