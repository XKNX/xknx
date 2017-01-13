import threading
import logging

import xknx

from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .xknx_config import XKNXConfig


_LOGGER = logging.getLogger(__name__)

class XKNXModule(object):
    """Representation of XKNX Object."""

    def __init__(self, hass, config):

        xknx_config = XKNXConfig(hass, config)

        self.xknx = xknx.XKNX()

        self.initialized = False
        self.lock = threading.Lock()
        self.hass = hass
        self.config_file = xknx_config.config_file()

    @staticmethod
    def telegram_received_callback(xknx, device, telegram):
        #print("{0}".format(device.name))
        pass

    def start(self):

        xknx.Config(self.xknx).read(file=self.config_file)

        self.xknx.start(
            telegram_received_callback=self.telegram_received_callback)

        self.hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)

        self.initialized = True


    def stop(self, event):
        """Shutdown XKNX correctly and stop all threads"""
        # TODO: Proper shutdown of xknx daemon not yet implemented
        pass
