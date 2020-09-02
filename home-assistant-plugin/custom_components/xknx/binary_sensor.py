"""Support for KNX/IP binary sensors."""
import asyncio

from xknx.devices import BinarySensor as XknxBinarySensor

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import callback

from . import DATA_XKNX


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up binary sensor(s) for KNX platform."""
    entities = []
    for device in hass.data[DATA_XKNX].xknx.devices:
        if isinstance(device, XknxBinarySensor):
            entities.append(KNXBinarySensor(device))
    async_add_entities(entities)


class KNXBinarySensor(BinarySensorEntity):
    """Representation of a KNX binary sensor."""

    CONTEXT_TIMEOUT = 1

    def __init__(self, device: XknxBinarySensor):
        """Initialize of KNX binary sensor."""
        self.device = device
        self._context_task = None

    def __del__(self):
        """Remove context task if still pending."""
        if self._context_task:
            self._context_task.cancel()

    @callback
    async def trigger_event(self, device: XknxBinarySensor, wait_time: int):
        """Call after context timeout is over and process event."""
        await asyncio.sleep(wait_time)
        self.hass.bus.fire(
            "knx_binary_sensor",
            {
                "entity_id": self.entity_id,
                "counter": device._count_set_on
                if device.state
                else device._count_set_off,
                "state": STATE_ON if device.state else STATE_OFF,
            },
        )

    @callback
    def async_register_callbacks(self):
        """Register callbacks to update hass after device was changed."""

        async def after_update_callback(device: XknxBinarySensor):
            """Call after device was updated."""

            if self._context_task:
                self._context_task.cancel()
            self._context_task = self.hass.loop.create_task(
                self.trigger_event(device, self.CONTEXT_TIMEOUT)
            )

            self.async_write_ha_state()

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
    def device_class(self):
        """Return the class of this sensor."""
        return self.device.device_class

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self.device.is_on()
