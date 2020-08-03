"""Support for KNX/IP covers."""
import voluptuous as vol
from xknx.devices import Cover as XknxCover

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    PLATFORM_SCHEMA,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import async_track_utc_time_change

from . import ATTR_DISCOVER_DEVICES, DATA_XKNX

CONF_MOVE_LONG_ADDRESS = "move_long_address"
CONF_MOVE_SHORT_ADDRESS = "move_short_address"
CONF_STOP_ADDRESS = "stop_address"
CONF_POSITION_ADDRESS = "position_address"
CONF_POSITION_STATE_ADDRESS = "position_state_address"
CONF_ANGLE_ADDRESS = "angle_address"
CONF_ANGLE_STATE_ADDRESS = "angle_state_address"
CONF_TRAVELLING_TIME_DOWN = "travelling_time_down"
CONF_TRAVELLING_TIME_UP = "travelling_time_up"
CONF_INVERT_POSITION = "invert_position"
CONF_INVERT_ANGLE = "invert_angle"

DEFAULT_TRAVEL_TIME = 25
DEFAULT_NAME = "KNX Cover"
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MOVE_LONG_ADDRESS): cv.string,
        vol.Optional(CONF_MOVE_SHORT_ADDRESS): cv.string,
        vol.Optional(CONF_STOP_ADDRESS): cv.string,
        vol.Optional(CONF_POSITION_ADDRESS): cv.string,
        vol.Optional(CONF_POSITION_STATE_ADDRESS): cv.string,
        vol.Optional(CONF_ANGLE_ADDRESS): cv.string,
        vol.Optional(CONF_ANGLE_STATE_ADDRESS): cv.string,
        vol.Optional(
            CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME
        ): cv.positive_int,
        vol.Optional(
            CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME
        ): cv.positive_int,
        vol.Optional(CONF_INVERT_POSITION, default=False): cv.boolean,
        vol.Optional(CONF_INVERT_ANGLE, default=False): cv.boolean,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up cover(s) for KNX platform."""
    if discovery_info is not None:
        async_add_entities_discovery(hass, discovery_info, async_add_entities)
    else:
        async_add_entities_config(hass, config, async_add_entities)


@callback
def async_add_entities_discovery(hass, discovery_info, async_add_entities):
    """Set up covers for KNX platform configured via xknx.yaml."""
    entities = []
    for device_name in discovery_info[ATTR_DISCOVER_DEVICES]:
        device = hass.data[DATA_XKNX].xknx.devices[device_name]
        entities.append(KNXCover(device))
    async_add_entities(entities)


@callback
def async_add_entities_config(hass, config, async_add_entities):
    """Set up cover for KNX platform configured within platform."""
    cover = XknxCover(
        hass.data[DATA_XKNX].xknx,
        name=config[CONF_NAME],
        group_address_long=config.get(CONF_MOVE_LONG_ADDRESS),
        group_address_short=config.get(CONF_MOVE_SHORT_ADDRESS),
        group_address_stop=config.get(CONF_STOP_ADDRESS),
        group_address_position_state=config.get(CONF_POSITION_STATE_ADDRESS),
        group_address_angle=config.get(CONF_ANGLE_ADDRESS),
        group_address_angle_state=config.get(CONF_ANGLE_STATE_ADDRESS),
        group_address_position=config.get(CONF_POSITION_ADDRESS),
        travel_time_down=config[CONF_TRAVELLING_TIME_DOWN],
        travel_time_up=config[CONF_TRAVELLING_TIME_UP],
        invert_position=config[CONF_INVERT_POSITION],
        invert_angle=config[CONF_INVERT_ANGLE],
    )

    hass.data[DATA_XKNX].xknx.devices.add(cover)
    async_add_entities([KNXCover(cover)])


class KNXCover(CoverEntity):
    """Representation of a KNX cover."""

    def __init__(self, device):
        """Initialize the cover."""
        self.device = device
        self._unsubscribe_auto_updater = None

    @callback
    def async_register_callbacks(self):
        """Register callbacks to update hass after device was changed."""

        async def after_update_callback(device):
            """Call after device was updated."""
            self.async_write_ha_state()
            if self.device.is_traveling():
                self.start_auto_updater()

        self.device.register_device_updated_cb(after_update_callback)

    async def async_added_to_hass(self):
        """Store register state change callback."""
        self.async_register_callbacks()

    async def async_update(self):
        """Request a state update from KNX bus."""
        await self.device.sync()

    @property
    def name(self):
        """Return the name of the KNX device."""
        return self.device.name

    @property
    def available(self):
        """Return True if entity is available."""
        return self.hass.data[DATA_XKNX].connected

    @property
    def should_poll(self):
        """No polling needed within KNX."""
        return False

    @property
    def supported_features(self):
        """Flag supported features."""
        supported_features = (
            SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION
        )
        if self.device.supports_stop:
            supported_features |= SUPPORT_STOP
        if self.device.supports_angle:
            supported_features |= SUPPORT_SET_TILT_POSITION
        return supported_features

    @property
    def current_cover_position(self):
        """Return current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        # In KNX 0 is open, 100 is closed.
        try:
            return 100 - self.device.current_position()
        except TypeError:
            return None

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self.device.is_closed()

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return self.device.is_opening()

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return self.device.is_closing()

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        await self.device.set_down()

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.device.set_up()

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            knx_position = 100 - kwargs[ATTR_POSITION]
            await self.device.set_position(knx_position)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self.device.stop()
        self.stop_auto_updater()

    @property
    def current_cover_tilt_position(self):
        """Return current position of cover tilt.
        None is unknown, 0 is closed, 100 is fully open.
        """
        # In KNX 0 is open, 100 is closed.
        if not self.device.supports_angle:
            return None
        try:
            return 100 - self.device.current_angle()
        except TypeError:
            return None

    async def async_set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        if ATTR_TILT_POSITION in kwargs:
            knx_tilt_position = 100 - kwargs[ATTR_TILT_POSITION]
            await self.device.set_angle(knx_tilt_position)

    def start_auto_updater(self):
        """Start the autoupdater to update Home Assistant while cover is moving."""
        if self._unsubscribe_auto_updater is None:
            self._unsubscribe_auto_updater = async_track_utc_time_change(
                self.hass, self.auto_updater_hook
            )

    def stop_auto_updater(self):
        """Stop the autoupdater."""
        if self._unsubscribe_auto_updater is not None:
            self._unsubscribe_auto_updater()
            self._unsubscribe_auto_updater = None

    @callback
    def auto_updater_hook(self, now):
        """Call for the autoupdater."""
        self.async_write_ha_state()
        if self.device.position_reached():
            self.stop_auto_updater()

        self.hass.add_job(self.device.auto_stop_if_necessary())
