import threading
import time
import logging

from xknx import XKNX,Config,TelegramProcessor,MulticastDaemon,StateUpdater

from homeassistant.const import EVENT_HOMEASSISTANT_STOP


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
    def telegram_received_callback(  xknx, device, telegram):
        #print("{0}".format(device.name))
        pass

    def start(self):

        Config(self.xknx).read(file=self.config_file)

        TelegramProcessor.start_thread(self.xknx, self.telegram_received_callback)
        MulticastDaemon.start_thread(self.xknx)
        StateUpdater.start_thread(self.xknx)

        self.hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)

        self.initialized = True


    def stop(self, event):
        """Shutdown XKNX correctly and stop all threads"""

        # Proper shutdown of xknx daemon not yet implemented
        pass

