import threading
import time
import logging

from homeassistant.components.switch import SwitchDevice

#import homeassistant.components.xknx as xknx
import custom_components.xknx as xknx

from xknx import Multicast,Devices,devices_,Config,Outlet

DOMAIN = 'xknx'

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):

    if xknx.xknx_wrapper is None or not xknx.xknx_wrapper.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    switches = []

    for device in devices_.devices:
        if type(device) == Outlet:
            switches.append(XKNX_Switch(device))   

    add_devices(switches)

    return True

class XKNX_Switch(SwitchDevice):
    """Representation of XKNX switches."""

    def __init__(self, device):
        self.device = device
        self.register_callbacks()

    def register_callbacks(self):
        def after_update_callback(device):
            self.update()
        self.device.after_update_callback = after_update_callback

    def update(self):
        self.update_ha_state()

    @property
    def name(self):
        return self.device.name

    @property
    def is_on(self):
        """Return true if pin is high/on."""
        return self.device.state

    def turn_on(self):
        """Turn the pin to high/on."""
        self.device.set_on()

    def turn_off(self):
        """Turn the pin to low/off."""
        self.device.set_off()

