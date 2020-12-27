"""Config validation."""
from enum import Enum

import voluptuous as vol

from ..devices.climate import SetpointShiftMode
from ..devices.light import ColorTempModes
from ..io import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from ..remote_value.remote_value_datetime import DateTimeType
from .config_validation import (
    boolean,
    ensure_group_address,
    ensure_individual_address,
    ensure_list,
    enum,
    isdir,
    match_all,
    port,
    positive_int,
    sensor_value_type,
    string,
    valid_entity_id,
)

CONF_STATE_UPDATE = "state_update"
CONF_ADDRESS = "address"
CONF_STATE_ADDRESS = "state_address"
CONF_SWITCH = "switch"


class ConnectionType(Enum):
    """Connection type to use."""

    TUNNELING = "tunneling"
    ROUTING = "routing"
    AUTO = "auto"


class RemoteValueSchema:
    """Schema validation for remote value configuration."""

    CONF_PASSIVE_GROUP_ADDRESSES = "passive_state_addresses"
    CONF_INVERT = "invert"

    DEFAULT_STATE_UPDATE = "expire 60"

    SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_ADDRESS): ensure_group_address,
            vol.Optional(CONF_STATE_ADDRESS): ensure_group_address,
            vol.Optional(CONF_STATE_UPDATE, default=DEFAULT_STATE_UPDATE): vol.Any(
                vol.All(vol.Coerce(int), vol.Range(min=2, max=1440)),
                boolean,
                string,
            ),
            vol.Optional(CONF_PASSIVE_GROUP_ADDRESSES): ensure_list,
        }
    )

    SCHEMA_INVERTABLE = SCHEMA.extend(
        {vol.Optional(CONF_INVERT, default=False): boolean}
    )


class BaseDeviceSchema:
    """Schema validation for all devices."""

    CONF_NAME = "name"
    CONF_FRIENDLY_NAME = "friendly_name"

    SCHEMA = vol.Schema(
        {
            vol.Required(CONF_NAME): string,
            vol.Optional(CONF_FRIENDLY_NAME): string,
        }
    )


class ConnectionSchema:
    """Voluptuous schema for KNX connection."""

    CONF_TYPE = "type"
    CONF_LOCAL_IP = "local_ip"
    CONF_HOST = "host"
    CONF_PORT = "port"

    SCHEMA = vol.Schema(
        {
            vol.Required(CONF_TYPE): enum(ConnectionType),
            vol.Optional(CONF_PORT, default=DEFAULT_MCAST_PORT): port,
            vol.Optional(CONF_LOCAL_IP): string,
            vol.Optional(CONF_HOST): string,
        }
    )


##
# Device schemas
##


class SwitchSchema:
    """Schema validation for switches."""

    CONF_RESET_AFTER = "reset_after"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_SWITCH): RemoteValueSchema.SCHEMA.extend(
                {vol.Required(CONF_ADDRESS): ensure_group_address}
            ),
            vol.Optional(CONF_RESET_AFTER): float,
        }
    )


class BinarySensorSchema:
    """Schema validation for binary sensors."""

    CONF_IGNORE_INTERNAL_STATE = "ignore_internal_state"
    CONF_CONTEXT_TIMEOUT = "context_timeout"
    CONF_RESET_AFTER = "reset_after"
    CONF_DEVICE_CLASS = "device_class"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_ADDRESS): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_IGNORE_INTERNAL_STATE, default=True): boolean,
            vol.Optional(CONF_CONTEXT_TIMEOUT, default=1.0): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=10)
            ),
            vol.Optional(CONF_DEVICE_CLASS): string,
            vol.Optional(CONF_RESET_AFTER): positive_int,
        }
    )


class LightSchema:
    """Voluptuous schema for KNX lights."""

    CONF_BRIGHTNESS = "brightness"
    CONF_RGBW = "rgbw"
    CONF_COLOR_TEMPERATURE = "color_temperature"
    CONF_COLOR = "color"
    CONF_INDIVIDUAL_COLORS = "individual_colors"

    CONF_COLOR_TEMP_MODE = "mode"
    CONF_MIN_KELVIN = "min_kelvin"
    CONF_MAX_KELVIN = "max_kelvin"

    CONF_RED = "red"
    CONF_GREEN = "green"
    CONF_BLUE = "blue"
    CONF_WHITE = "white"

    DEFAULT_COLOR_TEMP_MODE = "absolute"
    DEFAULT_MIN_KELVIN = 2700  # 370 mireds
    DEFAULT_MAX_KELVIN = 6000  # 166 mireds

    COLOR_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_SWITCH): RemoteValueSchema.SCHEMA,
            vol.Required(CONF_BRIGHTNESS): RemoteValueSchema.SCHEMA.extend(
                {vol.Required(CONF_ADDRESS): ensure_group_address}
            ),
        }
    )

    SCHEMA = vol.All(
        BaseDeviceSchema.SCHEMA.extend(
            {
                vol.Optional(CONF_SWITCH): RemoteValueSchema.SCHEMA.extend(
                    {vol.Required(CONF_ADDRESS): ensure_group_address}
                ),
                vol.Optional(CONF_BRIGHTNESS): RemoteValueSchema.SCHEMA.extend(
                    {vol.Required(CONF_ADDRESS): ensure_group_address}
                ),
                vol.Exclusive(CONF_RGBW, "color"): RemoteValueSchema.SCHEMA.extend(
                    {vol.Required(CONF_ADDRESS): ensure_group_address}
                ),
                vol.Exclusive(CONF_COLOR, "color"): RemoteValueSchema.SCHEMA.extend(
                    {vol.Required(CONF_ADDRESS): ensure_group_address}
                ),
                vol.Exclusive(CONF_INDIVIDUAL_COLORS, "color"): {
                    vol.Inclusive(CONF_RED, "colors"): COLOR_SCHEMA,
                    vol.Inclusive(CONF_GREEN, "colors"): COLOR_SCHEMA,
                    vol.Inclusive(CONF_BLUE, "colors"): COLOR_SCHEMA,
                    vol.Optional(CONF_WHITE): COLOR_SCHEMA,
                },
                vol.Optional(CONF_COLOR_TEMPERATURE): RemoteValueSchema.SCHEMA.extend(
                    {
                        vol.Required(CONF_ADDRESS): ensure_group_address,
                        vol.Optional(
                            CONF_COLOR_TEMP_MODE, default=DEFAULT_COLOR_TEMP_MODE
                        ): enum(ColorTempModes),
                        vol.Optional(
                            CONF_MIN_KELVIN, default=DEFAULT_MIN_KELVIN
                        ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                        vol.Optional(
                            CONF_MAX_KELVIN, default=DEFAULT_MAX_KELVIN
                        ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    }
                ),
            },
        ),
        vol.Any(
            vol.Schema(
                {
                    vol.Required(CONF_SWITCH): RemoteValueSchema.SCHEMA.extend(
                        {vol.Required(CONF_ADDRESS): object}
                    )
                },
                extra=vol.ALLOW_EXTRA,
            ),
            vol.Schema(
                {
                    vol.Required(CONF_INDIVIDUAL_COLORS): {
                        vol.Required(CONF_RED): {
                            vol.Required(CONF_SWITCH): {
                                vol.Required(CONF_ADDRESS): object
                            }
                        },
                        vol.Required(CONF_GREEN): {
                            vol.Required(CONF_SWITCH): {
                                vol.Required(CONF_ADDRESS): object
                            }
                        },
                        vol.Required(CONF_BLUE): {
                            vol.Required(CONF_SWITCH): {
                                vol.Required(CONF_ADDRESS): object
                            }
                        },
                    },
                },
                extra=vol.ALLOW_EXTRA,
            ),
        ),
    )


class FanSchema:
    """Voluptuous schema for KNX fans."""

    CONF_SPEED = "speed"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_SPEED): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
        }
    )


class CoverSchema:
    """Voluptuous schema for KNX covers."""

    CONF_LONG_MOVEMENT = "long_movement"
    CONF_SHORT_MOVEMENT = "short_movement"
    CONF_STOP_ADDRESS = "stop_address"
    CONF_POSITION = "position"
    CONF_ANGLE = "angle"
    CONF_TRAVELLING_TIME_DOWN = "travelling_time_down"
    CONF_TRAVELLING_TIME_UP = "travelling_time_up"

    DEFAULT_TRAVEL_TIME = 25

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(
                CONF_LONG_MOVEMENT
            ): RemoteValueSchema.SCHEMA_INVERTABLE.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                    vol.Remove(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(
                CONF_SHORT_MOVEMENT
            ): RemoteValueSchema.SCHEMA_INVERTABLE.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                    vol.Remove(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_STOP_ADDRESS): ensure_group_address,
            vol.Optional(CONF_POSITION): RemoteValueSchema.SCHEMA_INVERTABLE.extend(
                {vol.Required(CONF_ADDRESS): ensure_group_address}
            ),
            vol.Optional(CONF_ANGLE): RemoteValueSchema.SCHEMA_INVERTABLE.extend(
                {vol.Required(CONF_ADDRESS): ensure_group_address}
            ),
            vol.Optional(
                CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME
            ): positive_int,
            vol.Optional(
                CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME
            ): positive_int,
        }
    )


class ClimateSchema:
    """Voluptuous schema for KNX climates."""

    CONF_TARGET_TEMPERATURE = "target_temperature"
    CONF_SETPOINT_SHIFT = "setpoint_shift"
    CONF_SETPOINT_SHIFT_MODE = "mode"
    CONF_TEMPERATURE_STEP = "temperature_step"
    CONF_MIN_TEMP = "min"
    CONF_MAX_TEMP = "max"
    CONF_OPERATION_MODE = "operation_mode"
    CONF_BINARY_OPERATION_MODE = "binary_operation_mode"
    CONF_CONTROLLER_STATUS = "controller_status"
    CONF_CONTROLLER_MODE = "controller_mode"
    CONF_HEAT_COOL = "heat_cool"
    CONF_OPERATION_MODES = "operation_modes"
    CONF_ON_OFF = "on_off"

    CONF_FROST_PROTECTION_ADDRESS = "frost_protection_address"
    CONF_NIGHT_ADDRESS = "night_address"
    CONF_COMFORT_ADDRESS = "comfort_address"
    CONF_STANDBY_ADDRESS = "standby_address"

    # Map KNX operation modes to HA modes. This list might not be complete.
    OPERATION_MODES = {
        # Map DPT 20.105 HVAC control modes
        "Auto": None,
        "Heat": None,
        "Cool": None,
        "Off": None,
        "Fan only": None,
        "Dry": None,
    }

    PRESET_MODES = {
        # Map DPT 20.102 HVAC operating modes to HA presets
        "Frost Protection": None,
        "Night": None,
        "Standby": None,
        "Comfort": None,
    }

    DEFAULT_SETPOINT_SHIFT_MODE = "DPT6010"
    DEFAULT_SETPOINT_SHIFT_MAX = 6
    DEFAULT_SETPOINT_SHIFT_MIN = -6
    DEFAULT_TEMPERATURE_STEP = 0.1

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_TARGET_TEMPERATURE): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                    vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
                    vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
                }
            ),
            vol.Optional(CONF_SETPOINT_SHIFT): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                    vol.Optional(
                        CONF_SETPOINT_SHIFT_MODE, default=DEFAULT_SETPOINT_SHIFT_MODE
                    ): enum(SetpointShiftMode),
                    vol.Optional(
                        CONF_MIN_TEMP, default=DEFAULT_SETPOINT_SHIFT_MIN
                    ): vol.All(int, vol.Range(min=-32, max=0)),
                    vol.Optional(
                        CONF_MAX_TEMP, default=DEFAULT_SETPOINT_SHIFT_MAX
                    ): vol.All(int, vol.Range(min=0, max=32)),
                    vol.Optional(
                        CONF_TEMPERATURE_STEP, default=DEFAULT_TEMPERATURE_STEP
                    ): vol.All(float, vol.Range(min=0, max=2)),
                }
            ),
            vol.Optional(CONF_OPERATION_MODE): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_CONTROLLER_STATUS): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_CONTROLLER_MODE): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_HEAT_COOL): RemoteValueSchema.SCHEMA_INVERTABLE.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_ON_OFF): RemoteValueSchema.SCHEMA_INVERTABLE.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_BINARY_OPERATION_MODE): vol.Schema(
                {
                    vol.Optional(CONF_FROST_PROTECTION_ADDRESS): ensure_group_address,
                    vol.Optional(CONF_COMFORT_ADDRESS): ensure_group_address,
                    vol.Optional(CONF_NIGHT_ADDRESS): ensure_group_address,
                    vol.Optional(CONF_STANDBY_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_OPERATION_MODES): vol.All(
                ensure_list, [vol.In({**OPERATION_MODES, **PRESET_MODES})]
            ),
        }
    )


class WeatherSchema:
    """Voluptuous schema for KNX weather devices."""

    CONF_TEMPERATURE = "temperature"
    CONF_BRIGHTNESS_SOUTH = "brightness_south"
    CONF_BRIGHTNESS_NORTH = "brightness_north"
    CONF_BRIGHTNESS_EAST = "brightness_east"
    CONF_BRIGHTNESS_WEST = "brightness_west"
    CONF_RAIN_ALARM = "rain_alarm"
    CONF_WIND_ALARM = "wind_alarm"
    CONF_FROST_ALARM = "frost_alarm"
    CONF_WIND_SPEED = "wind_speed"
    CONF_DAY_NIGHT = "day_night"
    CONF_AIR_PRESSURE = "air_pressure"
    CONF_HUMIDITY = "humidity"
    CONF_EXPOSE_SENSORS = "expose_sensors"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_TEMPERATURE): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_BRIGHTNESS_SOUTH): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_BRIGHTNESS_NORTH): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_BRIGHTNESS_EAST): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_BRIGHTNESS_WEST): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_RAIN_ALARM): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_WIND_ALARM): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_FROST_ALARM): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_WIND_SPEED): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_DAY_NIGHT): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_AIR_PRESSURE): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_HUMIDITY): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                }
            ),
            vol.Optional(CONF_EXPOSE_SENSORS, default=False): boolean,
        }
    )


class DateTimeSchema:
    """Voluptuous schema for KNX date time devices."""

    CONF_TIME = "time"
    CONF_BROADCAST_TYPE = "broadcast_type"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_TIME): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                    vol.Remove(CONF_STATE_ADDRESS): ensure_group_address,
                    vol.Optional(CONF_BROADCAST_TYPE, default=DateTimeType.TIME): enum(
                        DateTimeType
                    ),
                }
            ),
        }
    )


class SceneSchema:
    """Voluptuous schema for KNX scenes."""

    CONF_SCENE = "scene"
    CONF_SCENE_NUMBER = "scene_number"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_SCENE): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                    vol.Remove(CONF_STATE_ADDRESS): ensure_group_address,
                    vol.Optional(CONF_STATE_UPDATE, default=False): False,
                    vol.Required(CONF_SCENE_NUMBER): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=64)
                    ),
                }
            ),
        }
    )


class NotificationSchema:
    """Voluptuous schema for KNX notifications."""

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_ADDRESS): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_ADDRESS): ensure_group_address,
                }
            ),
        }
    )


class ExposeSchema:
    """Voluptuous schema for KNX exposures."""

    CONF_TYPE = "type"
    CONF_ENTITY_ID = "entity_id"  # HA only
    CONF_ATTRIBUTE = "attribute"
    CONF_DEFAULT = "default"
    CONF_NAME = "name"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Remove(CONF_NAME): False,
            vol.Required(CONF_ADDRESS): ensure_group_address,
            vol.Required(CONF_TYPE): sensor_value_type,
            vol.Optional(CONF_DEFAULT): match_all,
            vol.Optional(CONF_ATTRIBUTE): string,
            vol.Optional(CONF_ENTITY_ID): valid_entity_id,
        }
    )


class SensorSchema:
    """Voluptuous schema for KNX sensors."""

    CONF_TYPE = "type"
    CONF_SENSOR = "sensor"

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_SENSOR): RemoteValueSchema.SCHEMA.extend(
                {
                    vol.Required(CONF_STATE_ADDRESS): ensure_group_address,
                    vol.Remove(CONF_ADDRESS): ensure_group_address,
                    vol.Required(CONF_TYPE): sensor_value_type,
                }
            ),
        }
    )


class XKNXSchema:
    """Voloptuous schema for XKNX config."""

    CONF_OWN_ADDRESS = "own_address"
    CONF_RATE_LIMIT = "rate_limit"
    CONF_VERSION = "version"
    CONF_LOG_DIRECTORY = "log_directory"
    CONF_FIRE_EVENT = "fire_event"
    CONF_FIRE_EVENT_FILTER = "fire_event_filter"
    CONF_MULTICAST_GROUP = "multicast_group"
    CONF_MULTICAST_PORT = "multicast_port"

    CONF_CONNECTION = "connection"
    CONF_BINARY_SENSOR = "binary_sensor"
    CONF_SWITCH = "switch"
    CONF_LIGHT = "light"
    CONF_FAN = "fan"
    CONF_COVER = "cover"
    CONF_CLIMATE = "climate"
    CONF_WEATHER = "weather"
    CONF_DATETIME = "datetime"
    CONF_NOTIFICATION = "notification"
    CONF_SCENE = "scene"
    CONF_EXPOSE = "expose_sensor"
    CONF_SENSOR = "sensor"

    SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_RATE_LIMIT, default=20): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=100)
            ),
            vol.Optional(CONF_VERSION, default=2): string,
            vol.Optional(CONF_OWN_ADDRESS): ensure_individual_address,
            vol.Optional(CONF_LOG_DIRECTORY): isdir,
            vol.Inclusive(CONF_FIRE_EVENT, "fire_ev"): boolean,
            vol.Inclusive(CONF_FIRE_EVENT_FILTER, "fire_ev"): vol.All(
                ensure_list, [string]
            ),
            vol.Optional(CONF_MULTICAST_GROUP, default=DEFAULT_MCAST_GRP): string,
            vol.Optional(CONF_MULTICAST_PORT, default=DEFAULT_MCAST_PORT): port,
            vol.Optional(CONF_CONNECTION): ConnectionSchema.SCHEMA,
            vol.Optional(CONF_BINARY_SENSOR): vol.All(
                ensure_list, [BinarySensorSchema.SCHEMA]
            ),
            vol.Optional(CONF_SWITCH): vol.All(ensure_list, [SwitchSchema.SCHEMA]),
            vol.Optional(CONF_LIGHT): vol.All(ensure_list, [LightSchema.SCHEMA]),
            vol.Optional(CONF_FAN): vol.All(ensure_list, [FanSchema.SCHEMA]),
            vol.Optional(CONF_COVER): vol.All(ensure_list, [CoverSchema.SCHEMA]),
            vol.Optional(CONF_CLIMATE): vol.All(ensure_list, [ClimateSchema.SCHEMA]),
            vol.Optional(CONF_WEATHER): vol.All(ensure_list, [WeatherSchema.SCHEMA]),
            vol.Optional(CONF_DATETIME): vol.All(ensure_list, [DateTimeSchema.SCHEMA]),
            vol.Optional(CONF_NOTIFICATION): vol.All(
                ensure_list, [NotificationSchema.SCHEMA]
            ),
            vol.Optional(CONF_SCENE): vol.All(ensure_list, [SceneSchema.SCHEMA]),
            vol.Optional(CONF_EXPOSE): vol.All(ensure_list, [ExposeSchema.SCHEMA]),
            vol.Optional(CONF_SENSOR): vol.All(ensure_list, [SensorSchema.SCHEMA]),
        }
    )
