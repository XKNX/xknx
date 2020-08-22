from homeassistant.const import (
    CONF_NAME,
    CONF_DEVICE_CLASS,
)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


class CoverSchema:
    """Voluptuous schema for KNX covers"""

    DEFAULT_TRAVEL_TIME = 25
    DEFAULT_COVER_NAME = "KNX Cover"

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

    SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_COVER_NAME): cv.string,
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


class BinarySensorSchema:
    """Voluptuous schema for KNX binary sensors"""

    DEFAULT_BINARY_SENSOR_NAME = "KNX Binary Sensor"

    CONF_STATE_ADDRESS = "state_address"
    CONF_SYNC_STATE = "sync_state"
    CONF_IGNORE_INTERNAL_STATE = "ignore_internal_state"
    CONF_AUTOMATION = "automation"
    CONF_HOOK = "hook"
    CONF_DEFAULT_HOOK = "on"
    CONF_COUNTER = "counter"
    CONF_DEFAULT_COUNTER = 1
    CONF_ACTION = "action"
    CONF_RESET_AFTER = "reset_after"

    AUTOMATION_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_HOOK, default=CONF_DEFAULT_HOOK): cv.string,
            vol.Optional(CONF_COUNTER, default=CONF_DEFAULT_COUNTER): cv.port,
            vol.Required(CONF_ACTION): cv.SCRIPT_SCHEMA,
        }
    )

    AUTOMATIONS_SCHEMA = vol.All(cv.ensure_list, [AUTOMATION_SCHEMA])

    SCHEMA = vol.All(
        cv.deprecated("significant_bit"),
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_BINARY_SENSOR_NAME): cv.string,
                vol.Optional(CONF_SYNC_STATE, default=True): vol.Any(
                    vol.All(vol.Coerce(int), vol.Range(min=2, max=1440)),
                    cv.boolean,
                    cv.string,
                ),
                vol.Optional(CONF_IGNORE_INTERNAL_STATE, default=False): cv.boolean,
                vol.Required(CONF_STATE_ADDRESS): cv.string,
                vol.Optional(CONF_DEVICE_CLASS): cv.string,
                vol.Optional(CONF_RESET_AFTER): cv.positive_int,
                vol.Optional(CONF_AUTOMATION): AUTOMATIONS_SCHEMA,
            }
        ),
    )
