"""Support for KNX/IP binary sensors."""
import voluptuous as vol
from xknx.devices import BinarySensor

from homeassistant.components.binary_sensor import PLATFORM_SCHEMA, BinarySensorEntity
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from homeassistant.const import CONF_NAME, CONF_DEVICE_CLASS

from .schema import BinarySensorSchema
from . import ATTR_DISCOVER_DEVICES, ATTR_DISCOVER_CONFIG, DATA_XKNX, KNXAutomation


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up binary sensor(s) for KNX platform."""
    if (
        discovery_info is not None
        and discovery_info.get(ATTR_DISCOVER_DEVICES) is not None
    ):
        async_add_entities_discovery(hass, discovery_info, async_add_entities)
    else:
        async_add_entities_config(
            hass, discovery_info[ATTR_DISCOVER_CONFIG], async_add_entities
        )


@callback
def async_add_entities_discovery(hass, discovery_info, async_add_entities):
    """Set up binary sensors for KNX platform configured via xknx.yaml."""
    entities = []
    for device_name in discovery_info[ATTR_DISCOVER_DEVICES]:
        device = hass.data[DATA_XKNX].xknx.devices[device_name]
        entities.append(KNXBinarySensor(device))
    async_add_entities(entities)


@callback
def async_add_entities_config(hass, config, async_add_entities):
    """Set up binary senor for KNX platform configured within platform."""
    binary_sensor = BinarySensor(
        hass.data[DATA_XKNX].xknx,
        name=config[CONF_NAME],
        group_address_state=config[BinarySensorSchema.CONF_STATE_ADDRESS],
        sync_state=config[BinarySensorSchema.CONF_SYNC_STATE],
        ignore_internal_state=config[BinarySensorSchema.CONF_IGNORE_INTERNAL_STATE],
        device_class=config.get(CONF_DEVICE_CLASS),
        reset_after=config.get(BinarySensorSchema.CONF_RESET_AFTER),
    )
    hass.data[DATA_XKNX].xknx.devices.add(binary_sensor)

    entity = KNXBinarySensor(binary_sensor)
    automations = config.get(BinarySensorSchema.CONF_AUTOMATION)
    if automations is not None:
        for automation in automations:
            counter = automation[BinarySensorSchema.CONF_COUNTER]
            hook = automation[BinarySensorSchema.CONF_HOOK]
            action = automation[BinarySensorSchema.CONF_ACTION]
            entity.automations.append(
                KNXAutomation(
                    hass=hass,
                    device=binary_sensor,
                    hook=hook,
                    action=action,
                    counter=counter,
                )
            )

    async_add_entities([entity])


class KNXBinarySensor(BinarySensorEntity):
    """Representation of a KNX binary sensor."""

    def __init__(self, device):
        """Initialize of KNX binary sensor."""
        self.device = device
        self.automations = []

    @callback
    def async_register_callbacks(self):
        """Register callbacks to update hass after device was changed."""

        async def after_update_callback(device):
            """Call after device was updated."""
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
