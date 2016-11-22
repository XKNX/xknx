import threading
import time
import os

from homeassistant.components.switch import SwitchDevice

from xknx import Multicast,Devices,devices_,Config,Outlet

DOMAIN = 'knx'

def worker(self,hass):
    """thread worker function"""
    i = 0
    while True:
        i=i+1
        hass.states.set('hello.world', "Status: %d" % i )
        time.sleep(5)
    return


def setup_platform(hass, config, add_devices, discovery_info=None):

    config_file='{0}/.homeassistant/xknx.yaml'.format( os.getenv("HOME") )
    Config.read(file=config_file)

    switches = []

    for device in devices_.devices:
        if type(device) == Outlet:
            switches.append(KNXSwitch(device))   
            print(device)

    add_devices(switches)


    def set_state_service(call):
        """Service to send a message."""
        print("RECEIVED MESSAGE")


    return True

class KNXSwitch(SwitchDevice):
    """Representation of KNX switches."""

    def __init__(self, device):

        self._state = True
        self.device = device

    @property
    def name(self):
        return self.device.name

    @property
    def is_on(self):
        """Return true if pin is high/on."""
        return self._state

    def turn_on(self):
        """Turn the pin to high/on."""
        self._state = True
        devices_.device_by_name(self.device.name).set_on()

    def turn_off(self):
        """Turn the pin to low/off."""
        self._state = False
        devices_.device_by_name(self.device.name).set_off()
