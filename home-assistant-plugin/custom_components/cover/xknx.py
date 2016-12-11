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

        self.register_callbacks()

    def register_callbacks(self):
        def after_update_callback(device):
            self.update()
        self.device.after_update_callback = after_update_callback

    def update(self):
        self.update_ha_state()

    @property
    def name(self):
        """Return the name of the cover."""
        return self.device.name

    @property
    def should_poll(self):
        """No polling needed for a demo cover."""
        return False

    @property
    def current_cover_position(self):
        """Return the current position of the cover."""
        return int( self.from_knx( self.device.position ) )

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.device.is_closed()

    def close_cover(self, **kwargs):
        """Close the cover."""
        if not self.device.is_closed():
            self.device.set_down()

    def open_cover(self, **kwargs):
        """Open the cover."""
        if not self.device.is_open():
            self.device.set_up()

    def set_cover_position(self, position, **kwargs):
        print("set_cover_position")
        """Move the cover to a specific position."""
        self.device.set_position( self.to_knx( position  ) )

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        if self.device.position is None:
            return
        self.device.set_short_down()

    #
    # HELPER FUNCTIONS
    #
    def from_knx(self, x):
        return round((x/256)*100)

    def to_knx(self, x):
        return round(x/100*255.5)

    #
    # UNUSED FUNCTIONS
    #
    def stop_cover_tilt(self, **kwargs):
        """Stop the cover tilt."""
        print("stop_cover_tilt - not implemented")

    def close_cover_tilt(self, **kwargs):
        """Close the cover tilt."""
        print("close_cover_tilt - not implemented")

    def set_cover_tilt_position(self, tilt_position, **kwargs):
        """Move the cover til to a specific position."""
        print("close_cover_tilt_position - not implemented")

    def open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        print("open_cover_tilt - not implemented")

    @property
    def current_cover_tilt_position(self):
        """Return the current tilt position of the cover."""
        return None

