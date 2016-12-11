import logging
from homeassistant.components.cover import CoverDevice
from homeassistant.helpers.event import track_utc_time_change

#import homeassistant.components.xknx as xknx
import custom_components.xknx as xknx

from xknx import Multicast,Devices,devices_,Config,Shutter

DOMAIN = 'xknx'

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_devices, discovery_info=None):

    if xknx.xknx_wrapper is None or not xknx.xknx_wrapper.initialized:
        _LOGGER.error('A connection has not been made to the XKNX controller.')
        return False

    shutters = []

    for device in devices_.devices:
        if type(device) == Shutter:
            shutters.append(XKNX_Cover(hass, device))

    add_devices(shutters)


class XKNX_Cover(CoverDevice):
    """Representation of a demo cover."""

    # pylint: disable=no-self-use
    def __init__(self, hass, device):
        """Initialize the cover."""
        self.hass = hass
        self.device = device
        self._position = 100 #TODO
        self._set_position = None
        self._set_tilt_position = None
        self._tilt_position = 10 #TODO
        self._closing = True
        self._closing_tilt = True
        self._unsub_listener_cover = None
        self._unsub_listener_cover_tilt = None
        self.register_callbacks()

    def register_callbacks(self):
        def after_update_callback(device):
            self.update()
        self.device.after_update_callback = after_update_callback
    @property
    def name(self):
        """Return the name of the cover."""
        return self.device.name

    @property
    def should_poll(self):
        """ polling cover."""
        return True

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return self._position

    @property
    def current_cover_tilt_position(self):
        """Return the current tilt position of the cover."""
        return self._tilt_position

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self._position is not None:
            if self.current_cover_position > 0:
                return False
            else:
                return True
        else:
            return None

    def close_cover(self, **kwargs):
        """Close the cover."""
        print("close_cover")
        if self._position in (0, None):
            return

        self.device.set_down()

        self._listen_cover()
        self._closing = True

    def close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        print("close_cover_tilt")
        if self._tilt_position in (0, None):
            return
        self.device.set_short_down()
        self._listen_cover_tilt()
        self._closing_tilt = True

    def open_cover(self, **kwargs):
        """Open the cover."""
        print("open_cover")
        if self._position in (100, None):
            return

        self.device.set_up()

        self._listen_cover()
        self._closing = False

    def open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        print("open_cover_tilt")
        if self._tilt_position in (100, None):
            return
        self.device.set_short_up()
        self._listen_cover_tilt()
        self._closing_tilt = False

    def set_cover_position(self, position, **kwargs):
        print("set_cover_position")
        """Move the cover to a specific position."""
        self._set_position = round(position, -1)
        if self._position == position:
            return

        self._listen_cover()
        self._closing = position < self._position
        if self._closing :
            self.device.set_down()
        else:
            self.device.set_up()
			
    def set_cover_tilt_position(self, tilt_position, **kwargs):
        """Move the cover til to a specific position."""
        print("set_cover_tilt_position")
        self._set_tilt_position = round(tilt_position, -1)
        if self._tilt_position == tilt_position:
            return

        self._listen_cover_tilt()
        self._closing_tilt = tilt_position < self._tilt_position
		

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        print("stop_cover");
        if self._position is None:
            return
        if self._unsub_listener_cover is not None:
            self._unsub_listener_cover()
            self._unsub_listener_cover = None
            self._set_position = None
            self.device.set_short_down()
        self.device.set_value_async('short', None)
        self.device.set_value_async('long', None)

    def stop_cover_tilt(self, **kwargs):
        """Stop the cover tilt."""
        if self._tilt_position is None:
            return

        if self._unsub_listener_cover_tilt is not None:
            self._unsub_listener_cover_tilt()
            self._unsub_listener_cover_tilt = None
            self._set_tilt_position = None

    def _listen_cover(self):
        """Listen for changes in cover."""
        if self._unsub_listener_cover is None:
            self._unsub_listener_cover = track_utc_time_change(
                self.hass, self._time_changed_cover)

    def _time_changed_cover(self, now):
        """Track time changes."""
        if self._closing:
            self._position -= 10
        else:
            self._position += 10
        #Limit
		
        if self._position > 100:
           self._position = 100
        if self._position < 0:
           self._position = 0
        if self._position in (100, 0, self._set_position):
            self.stop_cover()
        self.update_ha_state()

    def _listen_cover_tilt(self):
        """Listen for changes in cover tilt."""
        if self._unsub_listener_cover_tilt is None:
            self._unsub_listener_cover_tilt = track_utc_time_change(
                self.hass, self._time_changed_cover_tilt)

    def _time_changed_cover_tilt(self, now):
        """Track time changes."""
        if self._closing_tilt:
            self._tilt_position -= 10
        else:
            self._tilt_position += 10

        if self._tilt_position in (100, 0, self._set_tilt_position):
            self.stop_cover_tilt()

        self.update_ha_state()
		
    def update(self):
        """Update KNX Cover."""
        valuelong = self.device.value_long
        valueshort = self.device.value_short
		
        if valueshort != None:
          self._closing = False   
          if self._unsub_listener_cover is not None:
            self._unsub_listener_cover()
            self._unsub_listener_cover = None
            self._set_position = None
          self.device.set_value_async('short', None)
          self.device.set_value_async('long', None)
          
        if valuelong != None:
          if valuelong == 1:
            self._closing = True
            self._position = self._position - 1
          if valuelong == 0:
            self._closing = False
            self._position = self._position + 1			
          self.device.set_value_async('short', None)
          self.device.set_value_async('long', None)
          self._listen_cover()
        
