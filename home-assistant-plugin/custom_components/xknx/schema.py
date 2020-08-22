from homeassistant.const import (
    CONF_NAME
)

class CoverSchema:
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

    COVER_SCHEMA = vol.Schema(
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