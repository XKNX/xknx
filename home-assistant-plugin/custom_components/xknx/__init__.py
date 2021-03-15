"""Support KNX devices."""
import asyncio
import logging
from typing import Union

import voluptuous as vol
from xknx import XKNX
from xknx.core.telegram_queue import TelegramQueue
from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.exceptions import XKNXException
from xknx.io import (
    DEFAULT_MCAST_GRP,
    DEFAULT_MCAST_PORT,
    ConnectionConfig,
    ConnectionType,
)
from xknx.telegram import AddressFilter, GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from homeassistant.const import (
    CONF_HOST,
    CONF_PORT,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_RELOAD,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import async_get_platforms
from homeassistant.helpers.reload import async_integration_yaml_config
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ServiceCallType

from .const import DOMAIN, KNX_ADDRESS, SupportedPlatforms
from .expose import create_knx_exposure
from .factory import create_knx_device
from .schema import (
    BinarySensorSchema,
    ClimateSchema,
    ConnectionSchema,
    CoverSchema,
    ExposeSchema,
    FanSchema,
    LightSchema,
    NotifySchema,
    SceneSchema,
    SensorSchema,
    SwitchSchema,
    WeatherSchema,
    ga_validator,
    ia_validator,
)

_LOGGER = logging.getLogger(__name__)

CONF_XKNX_CONFIG = "config_file"

CONF_XKNX_ROUTING = "routing"
CONF_XKNX_TUNNELING = "tunneling"
CONF_XKNX_FIRE_EVENT = "fire_event"
CONF_XKNX_EVENT_FILTER = "event_filter"
CONF_XKNX_INDIVIDUAL_ADDRESS = "individual_address"
CONF_XKNX_MCAST_GRP = "multicast_group"
CONF_XKNX_MCAST_PORT = "multicast_port"
CONF_XKNX_STATE_UPDATER = "state_updater"
CONF_XKNX_RATE_LIMIT = "rate_limit"
CONF_XKNX_EXPOSE = "expose"

SERVICE_XKNX_SEND = "send"
SERVICE_XKNX_ATTR_PAYLOAD = "payload"
SERVICE_XKNX_ATTR_TYPE = "type"
SERVICE_XKNX_ATTR_REMOVE = "remove"
SERVICE_XKNX_EVENT_REGISTER = "event_register"
SERVICE_XKNX_EXPOSURE_REGISTER = "exposure_register"
SERVICE_XKNX_READ = "read"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            # deprecated since 2021.3
            cv.deprecated(CONF_XKNX_CONFIG),
            # deprecated since 2021.2
            cv.deprecated(CONF_XKNX_FIRE_EVENT),
            cv.deprecated("fire_event_filter", replacement_key=CONF_XKNX_EVENT_FILTER),
            vol.Schema(
                {
                    vol.Optional(CONF_XKNX_CONFIG): cv.string,
                    vol.Exclusive(
                        CONF_XKNX_ROUTING, "connection_type"
                    ): ConnectionSchema.ROUTING_SCHEMA,
                    vol.Exclusive(
                        CONF_XKNX_TUNNELING, "connection_type"
                    ): ConnectionSchema.TUNNELING_SCHEMA,
                    vol.Optional(CONF_XKNX_FIRE_EVENT): cv.boolean,
                    vol.Optional(CONF_XKNX_EVENT_FILTER, default=[]): vol.All(
                        cv.ensure_list, [cv.string]
                    ),
                    vol.Optional(
                        CONF_XKNX_INDIVIDUAL_ADDRESS, default=XKNX.DEFAULT_ADDRESS
                    ): ia_validator,
                    vol.Optional(
                        CONF_XKNX_MCAST_GRP, default=DEFAULT_MCAST_GRP
                    ): cv.string,
                    vol.Optional(
                        CONF_XKNX_MCAST_PORT, default=DEFAULT_MCAST_PORT
                    ): cv.port,
                    vol.Optional(CONF_XKNX_STATE_UPDATER, default=True): cv.boolean,
                    vol.Optional(CONF_XKNX_RATE_LIMIT, default=20): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=100)
                    ),
                    vol.Optional(CONF_XKNX_EXPOSE): vol.All(
                        cv.ensure_list, [ExposeSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.COVER.value): vol.All(
                        cv.ensure_list, [CoverSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.BINARY_SENSOR.value): vol.All(
                        cv.ensure_list, [BinarySensorSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.LIGHT.value): vol.All(
                        cv.ensure_list, [LightSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.CLIMATE.value): vol.All(
                        cv.ensure_list, [ClimateSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.NOTIFY.value): vol.All(
                        cv.ensure_list, [NotifySchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.SWITCH.value): vol.All(
                        cv.ensure_list, [SwitchSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.SENSOR.value): vol.All(
                        cv.ensure_list, [SensorSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.SCENE.value): vol.All(
                        cv.ensure_list, [SceneSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.WEATHER.value): vol.All(
                        cv.ensure_list, [WeatherSchema.SCHEMA]
                    ),
                    vol.Optional(SupportedPlatforms.FAN.value): vol.All(
                        cv.ensure_list, [FanSchema.SCHEMA]
                    ),
                }
            ),
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_XKNX_SEND_SCHEMA = vol.Any(
    vol.Schema(
        {
            vol.Required(KNX_ADDRESS): vol.All(
                cv.ensure_list,
                [ga_validator],
            ),
            vol.Required(SERVICE_XKNX_ATTR_PAYLOAD): cv.match_all,
            vol.Required(SERVICE_XKNX_ATTR_TYPE): vol.Any(int, float, str),
        }
    ),
    vol.Schema(
        # without type given payload is treated as raw bytes
        {
            vol.Required(KNX_ADDRESS): vol.All(
                cv.ensure_list,
                [ga_validator],
            ),
            vol.Required(SERVICE_XKNX_ATTR_PAYLOAD): vol.Any(
                cv.positive_int, [cv.positive_int]
            ),
        }
    ),
)

SERVICE_XKNX_READ_SCHEMA = vol.Schema(
    {
        vol.Required(KNX_ADDRESS): vol.All(
            cv.ensure_list,
            [ga_validator],
        )
    }
)

SERVICE_XKNX_EVENT_REGISTER_SCHEMA = vol.Schema(
    {
        vol.Required(KNX_ADDRESS): vol.All(
            cv.ensure_list,
            [ga_validator],
        ),
        vol.Optional(SERVICE_XKNX_ATTR_REMOVE, default=False): cv.boolean,
    }
)

SERVICE_XKNX_EXPOSURE_REGISTER_SCHEMA = vol.Any(
    ExposeSchema.SCHEMA.extend(
        {
            vol.Optional(SERVICE_XKNX_ATTR_REMOVE, default=False): cv.boolean,
        }
    ),
    vol.Schema(
        # for removing only `address` is required
        {
            vol.Required(KNX_ADDRESS): ga_validator,
            vol.Required(SERVICE_XKNX_ATTR_REMOVE): vol.All(cv.boolean, True),
        },
        extra=vol.ALLOW_EXTRA,
    ),
)


async def async_setup(hass, config):
    """Set up the KNX component."""
    try:
        knx_module = KNXModule(hass, config)
        hass.data[DOMAIN] = knx_module
        await knx_module.start()
    except XKNXException as ex:
        _LOGGER.warning("Could not connect to KNX interface: %s", ex)
        hass.components.persistent_notification.async_create(
            f"Could not connect to KNX interface: <br><b>{ex}</b>", title="KNX"
        )

    if CONF_XKNX_EXPOSE in config[DOMAIN]:
        for expose_config in config[DOMAIN][CONF_XKNX_EXPOSE]:
            knx_module.exposures.append(
                create_knx_exposure(hass, knx_module.xknx, expose_config)
            )

    for platform in SupportedPlatforms:
        if platform.value in config[DOMAIN]:
            for device_config in config[DOMAIN][platform.value]:
                create_knx_device(platform, knx_module.xknx, device_config)

    # We need to wait until all entities are loaded into the device list since they could also be created from other platforms
    for platform in SupportedPlatforms:
        hass.async_create_task(
            discovery.async_load_platform(hass, platform.value, DOMAIN, {}, config)
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_XKNX_SEND,
        knx_module.service_send_to_knx_bus,
        schema=SERVICE_XKNX_SEND_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_XKNX_READ,
        knx_module.service_read_to_knx_bus,
        schema=SERVICE_XKNX_READ_SCHEMA,
    )

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_XKNX_EVENT_REGISTER,
        knx_module.service_event_register_modify,
        schema=SERVICE_XKNX_EVENT_REGISTER_SCHEMA,
    )

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_XKNX_EXPOSURE_REGISTER,
        knx_module.service_exposure_register_modify,
        schema=SERVICE_XKNX_EXPOSURE_REGISTER_SCHEMA,
    )

    async def reload_service_handler(service_call: ServiceCallType) -> None:
        """Remove all KNX components and load new ones from config."""

        # First check for config file. If for some reason it is no longer there
        # or knx is no longer mentioned, stop the reload.
        config = await async_integration_yaml_config(hass, DOMAIN)

        if not config or DOMAIN not in config:
            return

        await knx_module.xknx.stop()

        await asyncio.gather(
            *[platform.async_reset() for platform in async_get_platforms(hass, DOMAIN)]
        )

        await async_setup(hass, config)

    async_register_admin_service(
        hass, DOMAIN, SERVICE_RELOAD, reload_service_handler, schema=vol.Schema({})
    )

    return True


class KNXModule:
    """Representation of KNX Object."""

    def __init__(self, hass, config):
        """Initialize of KNX module."""
        self.hass = hass
        self.config = config
        self.connected = False
        self.exposures = []
        self.service_exposures = {}

        self.init_xknx()
        self._knx_event_callback: TelegramQueue.Callback = self.register_callback()

    def init_xknx(self):
        """Initialize of KNX object."""
        self.xknx = XKNX(
            config=self.config_file(),
            own_address=self.config[DOMAIN][CONF_XKNX_INDIVIDUAL_ADDRESS],
            rate_limit=self.config[DOMAIN][CONF_XKNX_RATE_LIMIT],
            multicast_group=self.config[DOMAIN][CONF_XKNX_MCAST_GRP],
            multicast_port=self.config[DOMAIN][CONF_XKNX_MCAST_PORT],
            connection_config=self.connection_config(),
            state_updater=self.config[DOMAIN][CONF_XKNX_STATE_UPDATER],
        )

    async def start(self):
        """Start KNX object. Connect to tunneling or Routing device."""
        await self.xknx.start()
        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self.stop)
        self.connected = True

    async def stop(self, event):
        """Stop KNX object. Disconnect from tunneling or Routing device."""
        await self.xknx.stop()

    def config_file(self):
        """Resolve and return the full path of xknx.yaml if configured."""
        config_file = self.config[DOMAIN].get(CONF_XKNX_CONFIG)
        if not config_file:
            return None
        if not config_file.startswith("/"):
            return self.hass.config.path(config_file)
        return config_file

    def connection_config(self):
        """Return the connection_config."""
        if CONF_XKNX_TUNNELING in self.config[DOMAIN]:
            return self.connection_config_tunneling()
        if CONF_XKNX_ROUTING in self.config[DOMAIN]:
            return self.connection_config_routing()
        # config from xknx.yaml always has priority later on
        return ConnectionConfig(auto_reconnect=True)

    def connection_config_routing(self):
        """Return the connection_config if routing is configured."""
        local_ip = None
        # all configuration values are optional
        if self.config[DOMAIN][CONF_XKNX_ROUTING] is not None:
            local_ip = self.config[DOMAIN][CONF_XKNX_ROUTING].get(
                ConnectionSchema.CONF_XKNX_LOCAL_IP
            )
        return ConnectionConfig(
            connection_type=ConnectionType.ROUTING, local_ip=local_ip
        )

    def connection_config_tunneling(self):
        """Return the connection_config if tunneling is configured."""
        gateway_ip = self.config[DOMAIN][CONF_XKNX_TUNNELING][CONF_HOST]
        gateway_port = self.config[DOMAIN][CONF_XKNX_TUNNELING][CONF_PORT]
        local_ip = self.config[DOMAIN][CONF_XKNX_TUNNELING].get(
            ConnectionSchema.CONF_XKNX_LOCAL_IP
        )
        return ConnectionConfig(
            connection_type=ConnectionType.TUNNELING,
            gateway_ip=gateway_ip,
            gateway_port=gateway_port,
            local_ip=local_ip,
            auto_reconnect=True,
        )

    async def telegram_received_cb(self, telegram):
        """Call invoked after a KNX telegram was received."""
        data = None

        # Not all telegrams have serializable data.
        if isinstance(telegram.payload, (GroupValueWrite, GroupValueResponse)):
            data = telegram.payload.value.value

        self.hass.bus.async_fire(
            "knx_event",
            {
                "data": data,
                "destination": str(telegram.destination_address),
                "direction": telegram.direction.value,
                "source": str(telegram.source_address),
                "telegramtype": telegram.payload.__class__.__name__,
            },
        )

    def register_callback(self) -> TelegramQueue.Callback:
        """Register callback within XKNX TelegramQueue."""
        address_filters = list(
            map(AddressFilter, self.config[DOMAIN][CONF_XKNX_EVENT_FILTER])
        )
        return self.xknx.telegram_queue.register_telegram_received_cb(
            self.telegram_received_cb,
            address_filters=address_filters,
            group_addresses=[],
            match_for_outgoing=True,
        )

    async def service_event_register_modify(self, call):
        """Service for adding or removing a GroupAddress to the knx_event filter."""
        attr_address = call.data.get(KNX_ADDRESS)
        group_addresses = map(GroupAddress, attr_address)

        if call.data.get(SERVICE_XKNX_ATTR_REMOVE):
            for group_address in group_addresses:
                try:
                    self._knx_event_callback.group_addresses.remove(group_address)
                except ValueError:
                    _LOGGER.warning(
                        "Service event_register could not remove event for '%s'",
                        str(group_address),
                    )
        else:
            for group_address in group_addresses:
                if group_address not in self._knx_event_callback.group_addresses:
                    self._knx_event_callback.group_addresses.append(group_address)
                    _LOGGER.debug(
                        "Service event_register registered event for '%s'",
                        str(group_address),
                    )

    async def service_exposure_register_modify(self, call):
        """Service for adding or removing an exposure to KNX bus."""
        group_address = call.data.get(KNX_ADDRESS)

        if call.data.get(SERVICE_XKNX_ATTR_REMOVE):
            try:
                removed_exposure = self.service_exposures.pop(group_address)
            except KeyError as err:
                raise HomeAssistantError(
                    f"Could not find exposure for '{group_address}' to remove."
                ) from err
            else:
                removed_exposure.shutdown()
            return

        if group_address in self.service_exposures:
            replaced_exposure = self.service_exposures.pop(group_address)
            _LOGGER.warning(
                "Service exposure_register replacing already registered exposure for '%s' - %s",
                group_address,
                replaced_exposure.device.name,
            )
            replaced_exposure.shutdown()
        exposure = create_knx_exposure(self.hass, self.xknx, call.data)
        self.service_exposures[group_address] = exposure
        _LOGGER.debug(
            "Service exposure_register registered exposure for '%s' - %s",
            group_address,
            exposure.device.name,
        )

    async def service_send_to_knx_bus(self, call):
        """Service for sending an arbitrary KNX message to the KNX bus."""
        attr_address = call.data.get(KNX_ADDRESS)
        attr_payload = call.data.get(SERVICE_XKNX_ATTR_PAYLOAD)
        attr_type = call.data.get(SERVICE_XKNX_ATTR_TYPE)

        payload: Union[DPTBinary, DPTArray]
        if attr_type is not None:
            transcoder = DPTBase.parse_transcoder(attr_type)
            if transcoder is None:
                raise ValueError(f"Invalid type for knx.send service: {attr_type}")
            payload = DPTArray(transcoder.to_knx(attr_payload))
        elif isinstance(attr_payload, int):
            payload = DPTBinary(attr_payload)
        else:
            payload = DPTArray(attr_payload)

        for address in attr_address:
            telegram = Telegram(
                destination_address=GroupAddress(address),
                payload=GroupValueWrite(payload),
            )
            await self.xknx.telegrams.put(telegram)

    async def service_read_to_knx_bus(self, call):
        """Service for sending a GroupValueRead telegram to the KNX bus."""
        for address in call.data.get(KNX_ADDRESS):
            telegram = Telegram(
                destination_address=GroupAddress(address),
                payload=GroupValueRead(),
            )
            await self.xknx.telegrams.put(telegram)
