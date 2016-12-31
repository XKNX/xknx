import logging

import voluptuous as vol

from homeassistant.components.climate import (ClimateDevice, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_NAME, TEMP_CELSIUS, ATTR_TEMPERATURE)
import homeassistant.helpers.config_validation as cv

#import homeassistant.components.xknx as xknx_component
import custom_components.xknx as xknx_component

import xknx

DOMAIN = 'xknx'

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices_callback, discovery_info=None):

    if xknx_component.xknx_wrapper is None or not xknx_component.xknx_wrapper.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    thermostats = []

    for device in xknx_component.xknx_wrapper.xknx.devices.devices:
        if isinstance(device, xknx.Thermostat):
            thermostats.append(XKNX_Thermostat(hass, device))

    add_devices_callback(thermostats)

    return True


class XKNX_Thermostat(ClimateDevice):
    def __init__(self, hass, device):

        self._unit_of_measurement = TEMP_CELSIUS
        self._away = False  # not yet supported
        self._is_fan_on = False  # not yet supported
        self._current_temp = 15 # TODO: default temp from config 
        self._target_temp = 21 

        self.device = device

        self.register_callbacks()

    def register_callbacks(self):
        def after_update_callback(device):
            self.update()
        self.device.after_update_callback = after_update_callback

    @property
    def should_poll(self):
        """Polling not needed """
        return False

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temp

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        self._target_temp = temperature

        #TODO Sent to KNX bus
        
        self.update_ha_state()

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        raise NotImplementedError()

    def update(self):
        self._current_temp = self.device.temperature
        self.update_ha_state()

    @property
    def name(self):
        return self.device.name
