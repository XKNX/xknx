import threading
import logging
import asyncio
import xknx

from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .xknx_config import XKNXConfig


_LOGGER = logging.getLogger(__name__)

class XKNXModule(object):
    """Representation of XKNX Object."""

    def __init__(self, hass, config):

        xknx_config = XKNXConfig(hass, config)

        self.xknx = xknx.XKNX(loop=hass.loop, start=False)

        self.initialized = False
        self.lock = threading.Lock()
        self.hass = hass
        self.config_file = xknx_config.config_file()

    @staticmethod
    def telegram_received_callback(xknx, device, telegram):
        #print("{0}".format(device.name))
        pass

    @asyncio.coroutine
    def start(self):

        xknx.Config(self.xknx).read(file=self.config_file)

        yield from self.xknx.async_start(
            state_updater=True,
            telegram_received_callback=self.telegram_received_callback)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)

        self.initialized = True

    @asyncio.coroutine
    def stop(self, event):
        yield from self.xknx.async_stop()
