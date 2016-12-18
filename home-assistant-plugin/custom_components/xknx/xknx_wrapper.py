import threading
import time
import logging

from xknx import XKNX,Config,Multicast

_LOGGER = logging.getLogger(__name__)

class XKNX_Wrapper(object):
    """Representation of XKNX Object."""

    def __init__(self, hass, xknx_config):

        self.xknx = XKNX()

        self.initialized = False
        self.lock = threading.Lock()
        self.hass = hass
        self.config_file = xknx_config.config_file()

    @staticmethod
    def callback(  xknx, device, telegram):
        print("{0}".format(device.name))

    def start_knx_server(self,hass):
        Multicast(self.xknx).recv(self.callback)

    def start(self):

        Config(self.xknx).read(file=self.config_file)

        #TODO: Move to nicer class
        self.xknx.devices.update_thread_start(60)

        threading.Thread(target=self.start_knx_server, args=(self.hass,), name="XKNX Server").start()

        self.initialized = True

