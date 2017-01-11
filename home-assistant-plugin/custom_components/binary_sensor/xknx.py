import logging

#import homeassistant.components.xknx as xknx_component
import custom_components.xknx as xknx_component

import xknx

from homeassistant.components.binary_sensor import BinarySensorDevice

def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """Setup the XKNX binary sensor platform."""

    if xknx_component.xknx_wrapper is None or not xknx_component.xknx_wrapper.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    entities = []

    for device in xknx_component.xknx_wrapper.xknx.devices.devices:
        if isinstance(device, xknx.Sensor) and \
                device.is_binary():
            entities.append(XKNX_Binary_Sensor(hass, device))

    add_devices_callback(entities)

    return True


class XKNX_Binary_Sensor(BinarySensorDevice):

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
        print(self.device)
        self.update_ha_state()


    @property
    def name(self):
        """Return the name of the light if any."""
        return self.device.name


    @property
    def sensor_class(self):
        """Return the class of this sensor."""
        return self.device.sensor_class


    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.device.binary_state()
