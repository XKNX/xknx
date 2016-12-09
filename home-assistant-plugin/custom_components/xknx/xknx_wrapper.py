import threading
import time
import logging

from xknx import Config,Multicast, devices_

_LOGGER = logging.getLogger(__name__)

class XKNX_Wrapper(object):
    """Representation of XKNX Object."""

    def __init__(self, hass, xknx_config):
        self.initialized = False
        self.lock = threading.Lock()
        self.hass = hass
        self.config_file = xknx_config.config_file()
        self.i = 0

    @staticmethod
    def callback(  device, telegram):
        print("{0}".format(device.name))

    def start_knx_server(self,hass):
        Multicast().recv(self.callback)

    def start(self):

        Config.read(file=self.config_file)

        #TODO: Move to nicer class
        devices_.update_thread_start(20)

        threading.Thread(target=self.start_knx_server, args=(self.hass,), name="XKNX Server").start()

        self.initialized = True

