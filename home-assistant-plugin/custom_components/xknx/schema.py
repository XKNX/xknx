"""Voluptuous schemas for the KNX integration."""
from __future__ import annotations

from abc import ABC
from collections import OrderedDict
from typing import Any, ClassVar

import voluptuous as vol
from xknx import XKNX
from xknx.devices.climate import SetpointShiftMode
from xknx.dpt import DPTBase, DPTNumeric
from xknx.exceptions import CouldNotParseAddress
from xknx.io import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT
from xknx.telegram.address import IndividualAddress, parse_device_group_address

from homeassistant.components.binary_sensor import (
    DEVICE_CLASSES as BINARY_SENSOR_DEVICE_CLASSES,
)
from homeassistant.components.climate.const import HVAC_MODE_HEAT, HVAC_MODES
from homeassistant.components.cover import DEVICE_CLASSES as COVER_DEVICE_CLASSES
from homeassistant.components.sensor import CONF_STATE_CLASS, STATE_CLASSES_SCHEMA
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ENTITY_ID,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_TYPE,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_INVERT,
    CONF_RESET_AFTER,
    CONF_RESPOND_TO_READ,
    CONF_STATE_ADDRESS,
    CONF_SYNC_STATE,
    CONF_XKNX_EXPOSE,
    CONF_XKNX_INDIVIDUAL_ADDRESS,
    CONF_XKNX_ROUTING,
    CONF_XKNX_TUNNELING,
    CONTROLLER_MODES,
    KNX_ADDRESS,
    PRESET_MODES,
    ColorTempModes,
    SupportedPlatforms,
)

##################
# KNX VALIDATORS
##################


def ga_validator(value: Any) -> str | int:
    """Validate that value is parsable as GroupAddress or InternalGroupAddress."""
    if isinstance(value, (str, int)):
        try:
            parse_device_group_address(value)
            return value
        except CouldNotParseAddress:
            pass
    raise vol.Invalid(
        f"value '{value}' is not a valid KNX group address '<main>/<middle>/<sub>', '<main>/<sub>' "
        "or '<free>' (eg.'1/2/3', '9/234', '123'), nor xknx internal address 'i-<string>'."
    )


ga_list_validator = vol.All(cv.ensure_list, [ga_validator])

ia_validator = vol.Any(
    cv.matches_regex(IndividualAddress.ADDRESS_RE.pattern),
    vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
    msg="value does not match pattern for KNX individual address '<area>.<line>.<device>' (eg.'1.1.100')",
)


def number_limit_sub_validator(entity_config: OrderedDict) -> OrderedDict:
    """Validate a number entity configurations dependent on configured value type."""
    value_type = entity_config[CONF_TYPE]
    min_config: float | None = entity_config.get(NumberSchema.CONF_MIN)
    max_config: float | None = entity_config.get(NumberSchema.CONF_MAX)
    step_config: float | None = entity_config.get(NumberSchema.CONF_STEP)
    dpt_class = DPTNumeric.parse_transcoder(value_type)

    if dpt_class is None:
        raise vol.Invalid(f"'type: {value_type}' is not a valid numeric sensor type.")
    # Inifinity is not supported by Home Assistant frontend so user defined
    # config is required if if xknx DPTNumeric subclass defines it as limit.
    if min_config is None and dpt_class.value_min == float("-inf"):
        raise vol.Invalid(f"'min' key required for value type '{value_type}'")
    if min_config is not None and min_config < dpt_class.value_min:
        raise vol.Invalid(
            f"'min: {min_config}' undercuts possible minimum"
            f" of value type '{value_type}': {dpt_class.value_min}"
        )

    if max_config is None and dpt_class.value_max == float("inf"):
        raise vol.Invalid(f"'max' key required for value type '{value_type}'")
    if max_config is not None and max_config > dpt_class.value_max:
        raise vol.Invalid(
            f"'max: {max_config}' exceeds possible maximum"
            f" of value type '{value_type}': {dpt_class.value_max}"
        )

    if step_config is not None and step_config < dpt_class.resolution:
        raise vol.Invalid(
            f"'step: {step_config}' undercuts possible minimum step"
            f" of value type '{value_type}': {dpt_class.resolution}"
        )

    return entity_config


def numeric_type_validator(value: Any) -> str | int:
    """Validate that value is parsable as numeric sensor type."""
    if isinstance(value, (str, int)) and DPTNumeric.parse_transcoder(value) is not None:
        return value
    raise vol.Invalid(f"value '{value}' is not a valid numeric sensor type.")


def select_options_sub_validator(entity_config: OrderedDict) -> OrderedDict:
    """Validate a select entity options configuration."""
    options_seen = set()
    payloads_seen = set()
    payload_length = entity_config[SelectSchema.CONF_PAYLOAD_LENGTH]
    if payload_length == 0:
        max_payload = 0x3F
    else:
        max_payload = 256 ** payload_length - 1

    for opt in entity_config[SelectSchema.CONF_OPTIONS]:
        option = opt[SelectSchema.CONF_OPTION]
        payload = opt[SelectSchema.CONF_PAYLOAD]
        if payload > max_payload:
            raise vol.Invalid(
                f"'payload: {payload}' for 'option: {option}' exceeds possible"
                f" maximum of 'payload_length: {payload_length}': {max_payload}"
            )
        if option in options_seen:
            raise vol.Invalid(f"duplicate item for 'option' not allowed: {option}")
        options_seen.add(option)
        if payload in payloads_seen:
            raise vol.Invalid(f"duplicate item for 'payload' not allowed: {payload}")
        payloads_seen.add(payload)
    return entity_config


def sensor_type_validator(value: Any) -> str | int:
    """Validate that value is parsable as sensor type."""
    if isinstance(value, (str, int)) and DPTBase.parse_transcoder(value) is not None:
        return value
    raise vol.Invalid(f"value '{value}' is not a valid sensor type.")


sync_state_validator = vol.Any(
    vol.All(vol.Coerce(int), vol.Range(min=2, max=1440)),
    cv.boolean,
    cv.matches_regex(r"^(init|expire|every)( \d*)?$"),
)


##############
# CONNECTION
##############


class ConnectionSchema:
    """Voluptuous schema for KNX connection."""

    CONF_XKNX_LOCAL_IP = "local_ip"
    CONF_XKNX_MCAST_GRP = "multicast_group"
    CONF_XKNX_MCAST_PORT = "multicast_port"
    CONF_XKNX_RATE_LIMIT = "rate_limit"
    CONF_XKNX_ROUTE_BACK = "route_back"
    CONF_XKNX_STATE_UPDATER = "state_updater"

    TUNNELING_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_PORT, default=DEFAULT_MCAST_PORT): cv.port,
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(CONF_XKNX_LOCAL_IP): cv.string,
            vol.Optional(CONF_XKNX_ROUTE_BACK, default=False): cv.boolean,
        }
    )

    ROUTING_SCHEMA = vol.Maybe(
        vol.Schema({vol.Optional(CONF_XKNX_LOCAL_IP): cv.string})
    )

    SCHEMA = {
        vol.Exclusive(CONF_XKNX_ROUTING, "connection_type"): ROUTING_SCHEMA,
        vol.Exclusive(CONF_XKNX_TUNNELING, "connection_type"): TUNNELING_SCHEMA,
        vol.Optional(
            CONF_XKNX_INDIVIDUAL_ADDRESS, default=XKNX.DEFAULT_ADDRESS
        ): ia_validator,
        vol.Optional(CONF_XKNX_MCAST_GRP, default=DEFAULT_MCAST_GRP): cv.string,
        vol.Optional(CONF_XKNX_MCAST_PORT, default=DEFAULT_MCAST_PORT): cv.port,
        vol.Optional(CONF_XKNX_STATE_UPDATER, default=True): cv.boolean,
        vol.Optional(CONF_XKNX_RATE_LIMIT, default=20): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=100)
        ),
    }


#############
# PLATFORMS
#############


class KNXPlatformSchema(ABC):
    """Voluptuous schema for KNX platform entity configuration."""

    PLATFORM_NAME: ClassVar[str]
    ENTITY_SCHEMA: ClassVar[vol.Schema]

    @classmethod
    def platform_node(cls) -> dict[vol.Optional, vol.All]:
        """Return a schema node for the platform."""
        return {
            vol.Optional(cls.PLATFORM_NAME): vol.All(
                cv.ensure_list, [cls.ENTITY_SCHEMA]
            )
        }


class BinarySensorSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX binary sensors."""

    PLATFORM_NAME = SupportedPlatforms.BINARY_SENSOR.value

    CONF_STATE_ADDRESS = CONF_STATE_ADDRESS
    CONF_SYNC_STATE = CONF_SYNC_STATE
    CONF_INVERT = CONF_INVERT
    CONF_IGNORE_INTERNAL_STATE = "ignore_internal_state"
    CONF_CONTEXT_TIMEOUT = "context_timeout"
    CONF_RESET_AFTER = CONF_RESET_AFTER

    DEFAULT_NAME = "KNX Binary Sensor"

    ENTITY_SCHEMA = vol.All(
        # deprecated since September 2020
        cv.deprecated("significant_bit"),
        cv.deprecated("automation"),
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_SYNC_STATE, default=True): sync_state_validator,
                vol.Optional(CONF_IGNORE_INTERNAL_STATE, default=False): cv.boolean,
                vol.Optional(CONF_INVERT, default=False): cv.boolean,
                vol.Required(CONF_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_CONTEXT_TIMEOUT): vol.All(
                    vol.Coerce(float), vol.Range(min=0, max=10)
                ),
                vol.Optional(CONF_DEVICE_CLASS): vol.In(BINARY_SENSOR_DEVICE_CLASSES),
                vol.Optional(CONF_RESET_AFTER): cv.positive_float,
            }
        ),
    )


class ClimateSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX climate devices."""

    PLATFORM_NAME = SupportedPlatforms.CLIMATE.value

    CONF_ACTIVE_STATE_ADDRESS = "active_state_address"
    CONF_SETPOINT_SHIFT_ADDRESS = "setpoint_shift_address"
    CONF_SETPOINT_SHIFT_STATE_ADDRESS = "setpoint_shift_state_address"
    CONF_SETPOINT_SHIFT_MODE = "setpoint_shift_mode"
    CONF_SETPOINT_SHIFT_MAX = "setpoint_shift_max"
    CONF_SETPOINT_SHIFT_MIN = "setpoint_shift_min"
    CONF_TEMPERATURE_ADDRESS = "temperature_address"
    CONF_TEMPERATURE_STEP = "temperature_step"
    CONF_TARGET_TEMPERATURE_ADDRESS = "target_temperature_address"
    CONF_TARGET_TEMPERATURE_STATE_ADDRESS = "target_temperature_state_address"
    CONF_OPERATION_MODE_ADDRESS = "operation_mode_address"
    CONF_OPERATION_MODE_STATE_ADDRESS = "operation_mode_state_address"
    CONF_CONTROLLER_STATUS_ADDRESS = "controller_status_address"
    CONF_CONTROLLER_STATUS_STATE_ADDRESS = "controller_status_state_address"
    CONF_CONTROLLER_MODE_ADDRESS = "controller_mode_address"
    CONF_CONTROLLER_MODE_STATE_ADDRESS = "controller_mode_state_address"
    CONF_COMMAND_VALUE_STATE_ADDRESS = "command_value_state_address"
    CONF_HEAT_COOL_ADDRESS = "heat_cool_address"
    CONF_HEAT_COOL_STATE_ADDRESS = "heat_cool_state_address"
    CONF_OPERATION_MODE_FROST_PROTECTION_ADDRESS = (
        "operation_mode_frost_protection_address"
    )
    CONF_OPERATION_MODE_NIGHT_ADDRESS = "operation_mode_night_address"
    CONF_OPERATION_MODE_COMFORT_ADDRESS = "operation_mode_comfort_address"
    CONF_OPERATION_MODE_STANDBY_ADDRESS = "operation_mode_standby_address"
    CONF_OPERATION_MODES = "operation_modes"
    CONF_CONTROLLER_MODES = "controller_modes"
    CONF_DEFAULT_CONTROLLER_MODE = "default_controller_mode"
    CONF_ON_OFF_ADDRESS = "on_off_address"
    CONF_ON_OFF_STATE_ADDRESS = "on_off_state_address"
    CONF_ON_OFF_INVERT = "on_off_invert"
    CONF_MIN_TEMP = "min_temp"
    CONF_MAX_TEMP = "max_temp"

    DEFAULT_NAME = "KNX Climate"
    DEFAULT_SETPOINT_SHIFT_MODE = "DPT6010"
    DEFAULT_SETPOINT_SHIFT_MAX = 6
    DEFAULT_SETPOINT_SHIFT_MIN = -6
    DEFAULT_TEMPERATURE_STEP = 0.1
    DEFAULT_ON_OFF_INVERT = False

    ENTITY_SCHEMA = vol.All(
        # deprecated since September 2020
        cv.deprecated("setpoint_shift_step", replacement_key=CONF_TEMPERATURE_STEP),
        # deprecated since 2021.6
        cv.deprecated("create_temperature_sensors"),
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(
                    CONF_SETPOINT_SHIFT_MAX, default=DEFAULT_SETPOINT_SHIFT_MAX
                ): vol.All(int, vol.Range(min=0, max=32)),
                vol.Optional(
                    CONF_SETPOINT_SHIFT_MIN, default=DEFAULT_SETPOINT_SHIFT_MIN
                ): vol.All(int, vol.Range(min=-32, max=0)),
                vol.Optional(
                    CONF_TEMPERATURE_STEP, default=DEFAULT_TEMPERATURE_STEP
                ): vol.All(float, vol.Range(min=0, max=2)),
                vol.Required(CONF_TEMPERATURE_ADDRESS): ga_list_validator,
                vol.Required(CONF_TARGET_TEMPERATURE_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_TARGET_TEMPERATURE_ADDRESS): ga_list_validator,
                vol.Inclusive(
                    CONF_SETPOINT_SHIFT_ADDRESS,
                    "setpoint_shift",
                    msg="'setpoint_shift_address' and 'setpoint_shift_state_address' "
                    "are required for setpoint_shift configuration",
                ): ga_list_validator,
                vol.Inclusive(
                    CONF_SETPOINT_SHIFT_STATE_ADDRESS,
                    "setpoint_shift",
                    msg="'setpoint_shift_address' and 'setpoint_shift_state_address' "
                    "are required for setpoint_shift configuration",
                ): ga_list_validator,
                vol.Optional(CONF_SETPOINT_SHIFT_MODE): vol.Maybe(
                    vol.All(vol.Upper, cv.enum(SetpointShiftMode))
                ),
                vol.Optional(CONF_ACTIVE_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_COMMAND_VALUE_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_OPERATION_MODE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_OPERATION_MODE_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_CONTROLLER_STATUS_ADDRESS): ga_list_validator,
                vol.Optional(CONF_CONTROLLER_STATUS_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_CONTROLLER_MODE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_CONTROLLER_MODE_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_HEAT_COOL_ADDRESS): ga_list_validator,
                vol.Optional(CONF_HEAT_COOL_STATE_ADDRESS): ga_list_validator,
                vol.Optional(
                    CONF_OPERATION_MODE_FROST_PROTECTION_ADDRESS
                ): ga_list_validator,
                vol.Optional(CONF_OPERATION_MODE_NIGHT_ADDRESS): ga_list_validator,
                vol.Optional(CONF_OPERATION_MODE_COMFORT_ADDRESS): ga_list_validator,
                vol.Optional(CONF_OPERATION_MODE_STANDBY_ADDRESS): ga_list_validator,
                vol.Optional(CONF_ON_OFF_ADDRESS): ga_list_validator,
                vol.Optional(CONF_ON_OFF_STATE_ADDRESS): ga_list_validator,
                vol.Optional(
                    CONF_ON_OFF_INVERT, default=DEFAULT_ON_OFF_INVERT
                ): cv.boolean,
                vol.Optional(CONF_OPERATION_MODES): vol.All(
                    cv.ensure_list, [vol.In(PRESET_MODES)]
                ),
                vol.Optional(CONF_CONTROLLER_MODES): vol.All(
                    cv.ensure_list, [vol.In(CONTROLLER_MODES)]
                ),
                vol.Optional(
                    CONF_DEFAULT_CONTROLLER_MODE, default=HVAC_MODE_HEAT
                ): vol.In(HVAC_MODES),
                vol.Optional(CONF_MIN_TEMP): vol.Coerce(float),
                vol.Optional(CONF_MAX_TEMP): vol.Coerce(float),
            }
        ),
    )


class CoverSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX covers."""

    PLATFORM_NAME = SupportedPlatforms.COVER.value

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

    ENTITY_SCHEMA = vol.All(
        vol.Schema(
            {
                vol.Required(
                    vol.Any(CONF_MOVE_LONG_ADDRESS, CONF_POSITION_ADDRESS),
                    msg=f"At least one of '{CONF_MOVE_LONG_ADDRESS}' or '{CONF_POSITION_ADDRESS}' is required.",
                ): object,
            },
            extra=vol.ALLOW_EXTRA,
        ),
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_MOVE_LONG_ADDRESS): ga_list_validator,
                vol.Optional(CONF_MOVE_SHORT_ADDRESS): ga_list_validator,
                vol.Optional(CONF_STOP_ADDRESS): ga_list_validator,
                vol.Optional(CONF_POSITION_ADDRESS): ga_list_validator,
                vol.Optional(CONF_POSITION_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_ANGLE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_ANGLE_STATE_ADDRESS): ga_list_validator,
                vol.Optional(
                    CONF_TRAVELLING_TIME_DOWN, default=DEFAULT_TRAVEL_TIME
                ): cv.positive_float,
                vol.Optional(
                    CONF_TRAVELLING_TIME_UP, default=DEFAULT_TRAVEL_TIME
                ): cv.positive_float,
                vol.Optional(CONF_INVERT_POSITION, default=False): cv.boolean,
                vol.Optional(CONF_INVERT_ANGLE, default=False): cv.boolean,
                vol.Optional(CONF_DEVICE_CLASS): vol.In(COVER_DEVICE_CLASSES),
            }
        ),
    )


class ExposeSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX exposures."""

    PLATFORM_NAME = CONF_XKNX_EXPOSE

    CONF_XKNX_EXPOSE_TYPE = CONF_TYPE
    CONF_XKNX_EXPOSE_ATTRIBUTE = "attribute"
    CONF_XKNX_EXPOSE_BINARY = "binary"
    CONF_XKNX_EXPOSE_DEFAULT = "default"
    EXPOSE_TIME_TYPES = [
        "time",
        "date",
        "datetime",
    ]

    EXPOSE_TIME_SCHEMA = vol.Schema(
        {
            vol.Required(CONF_XKNX_EXPOSE_TYPE): vol.All(
                cv.string, str.lower, vol.In(EXPOSE_TIME_TYPES)
            ),
            vol.Required(KNX_ADDRESS): ga_validator,
        }
    )
    EXPOSE_SENSOR_SCHEMA = vol.Schema(
        {
            vol.Required(CONF_XKNX_EXPOSE_TYPE): vol.Any(
                CONF_XKNX_EXPOSE_BINARY, sensor_type_validator
            ),
            vol.Required(KNX_ADDRESS): ga_validator,
            vol.Required(CONF_ENTITY_ID): cv.entity_id,
            vol.Optional(CONF_XKNX_EXPOSE_ATTRIBUTE): cv.string,
            vol.Optional(CONF_XKNX_EXPOSE_DEFAULT): cv.match_all,
        }
    )
    ENTITY_SCHEMA = vol.Any(EXPOSE_SENSOR_SCHEMA, EXPOSE_TIME_SCHEMA)


class FanSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX fans."""

    PLATFORM_NAME = SupportedPlatforms.FAN.value

    CONF_STATE_ADDRESS = CONF_STATE_ADDRESS
    CONF_OSCILLATION_ADDRESS = "oscillation_address"
    CONF_OSCILLATION_STATE_ADDRESS = "oscillation_state_address"
    CONF_MAX_STEP = "max_step"

    DEFAULT_NAME = "KNX Fan"

    ENTITY_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Required(KNX_ADDRESS): ga_list_validator,
            vol.Optional(CONF_STATE_ADDRESS): ga_list_validator,
            vol.Optional(CONF_OSCILLATION_ADDRESS): ga_list_validator,
            vol.Optional(CONF_OSCILLATION_STATE_ADDRESS): ga_list_validator,
            vol.Optional(CONF_MAX_STEP): cv.byte,
        }
    )


class LightSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX lights."""

    PLATFORM_NAME = SupportedPlatforms.LIGHT.value

    CONF_STATE_ADDRESS = CONF_STATE_ADDRESS
    CONF_BRIGHTNESS_ADDRESS = "brightness_address"
    CONF_BRIGHTNESS_STATE_ADDRESS = "brightness_state_address"
    CONF_COLOR_ADDRESS = "color_address"
    CONF_COLOR_STATE_ADDRESS = "color_state_address"
    CONF_COLOR_TEMP_ADDRESS = "color_temperature_address"
    CONF_COLOR_TEMP_STATE_ADDRESS = "color_temperature_state_address"
    CONF_COLOR_TEMP_MODE = "color_temperature_mode"
    CONF_HUE_ADDRESS = "hue_address"
    CONF_HUE_STATE_ADDRESS = "hue_state_address"
    CONF_RGBW_ADDRESS = "rgbw_address"
    CONF_RGBW_STATE_ADDRESS = "rgbw_state_address"
    CONF_SATURATION_ADDRESS = "saturation_address"
    CONF_SATURATION_STATE_ADDRESS = "saturation_state_address"
    CONF_XYY_ADDRESS = "xyy_address"
    CONF_XYY_STATE_ADDRESS = "xyy_state_address"
    CONF_MIN_KELVIN = "min_kelvin"
    CONF_MAX_KELVIN = "max_kelvin"

    DEFAULT_NAME = "KNX Light"
    DEFAULT_COLOR_TEMP_MODE = "absolute"
    DEFAULT_MIN_KELVIN = 2700  # 370 mireds
    DEFAULT_MAX_KELVIN = 6000  # 166 mireds

    CONF_INDIVIDUAL_COLORS = "individual_colors"
    CONF_RED = "red"
    CONF_GREEN = "green"
    CONF_BLUE = "blue"
    CONF_WHITE = "white"

    _hs_color_inclusion_msg = (
        "'hue_address', 'saturation_address' and 'brightness_address'"
        " are required for hs_color configuration"
    )
    HS_COLOR_SCHEMA = {
        vol.Optional(CONF_HUE_ADDRESS): ga_list_validator,
        vol.Optional(CONF_HUE_STATE_ADDRESS): ga_list_validator,
        vol.Optional(CONF_SATURATION_ADDRESS): ga_list_validator,
        vol.Optional(CONF_SATURATION_STATE_ADDRESS): ga_list_validator,
    }

    INDIVIDUAL_COLOR_SCHEMA = vol.Schema(
        {
            vol.Optional(KNX_ADDRESS): ga_list_validator,
            vol.Optional(CONF_STATE_ADDRESS): ga_list_validator,
            vol.Required(CONF_BRIGHTNESS_ADDRESS): ga_list_validator,
            vol.Optional(CONF_BRIGHTNESS_STATE_ADDRESS): ga_list_validator,
        }
    )

    ENTITY_SCHEMA = vol.All(
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(KNX_ADDRESS): ga_list_validator,
                vol.Optional(CONF_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_BRIGHTNESS_ADDRESS): ga_list_validator,
                vol.Optional(CONF_BRIGHTNESS_STATE_ADDRESS): ga_list_validator,
                vol.Exclusive(CONF_INDIVIDUAL_COLORS, "color"): {
                    vol.Inclusive(
                        CONF_RED,
                        "individual_colors",
                        msg="'red', 'green' and 'blue' are required for individual colors configuration",
                    ): INDIVIDUAL_COLOR_SCHEMA,
                    vol.Inclusive(
                        CONF_GREEN,
                        "individual_colors",
                        msg="'red', 'green' and 'blue' are required for individual colors configuration",
                    ): INDIVIDUAL_COLOR_SCHEMA,
                    vol.Inclusive(
                        CONF_BLUE,
                        "individual_colors",
                        msg="'red', 'green' and 'blue' are required for individual colors configuration",
                    ): INDIVIDUAL_COLOR_SCHEMA,
                    vol.Optional(CONF_WHITE): INDIVIDUAL_COLOR_SCHEMA,
                },
                vol.Exclusive(CONF_COLOR_ADDRESS, "color"): ga_list_validator,
                vol.Optional(CONF_COLOR_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_COLOR_TEMP_ADDRESS): ga_list_validator,
                vol.Optional(CONF_COLOR_TEMP_STATE_ADDRESS): ga_list_validator,
                vol.Optional(
                    CONF_COLOR_TEMP_MODE, default=DEFAULT_COLOR_TEMP_MODE
                ): vol.All(vol.Upper, cv.enum(ColorTempModes)),
                **HS_COLOR_SCHEMA,
                vol.Exclusive(CONF_RGBW_ADDRESS, "color"): ga_list_validator,
                vol.Optional(CONF_RGBW_STATE_ADDRESS): ga_list_validator,
                vol.Exclusive(CONF_XYY_ADDRESS, "color"): ga_list_validator,
                vol.Optional(CONF_XYY_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_MIN_KELVIN, default=DEFAULT_MIN_KELVIN): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
                vol.Optional(CONF_MAX_KELVIN, default=DEFAULT_MAX_KELVIN): vol.All(
                    vol.Coerce(int), vol.Range(min=1)
                ),
            }
        ),
        vol.Any(
            vol.Schema(
                {vol.Required(KNX_ADDRESS): object},
                extra=vol.ALLOW_EXTRA,
            ),
            vol.Schema(  # brightness addresses are required in INDIVIDUAL_COLOR_SCHEMA
                {vol.Required(CONF_INDIVIDUAL_COLORS): object},
                extra=vol.ALLOW_EXTRA,
            ),
            msg="either 'address' or 'individual_colors' is required",
        ),
        vol.Any(
            vol.Schema(  # 'brightness' is non-optional for hs-color
                {
                    vol.Inclusive(
                        CONF_BRIGHTNESS_ADDRESS, "hs_color", msg=_hs_color_inclusion_msg
                    ): object,
                    vol.Inclusive(
                        CONF_HUE_ADDRESS, "hs_color", msg=_hs_color_inclusion_msg
                    ): object,
                    vol.Inclusive(
                        CONF_SATURATION_ADDRESS, "hs_color", msg=_hs_color_inclusion_msg
                    ): object,
                },
                extra=vol.ALLOW_EXTRA,
            ),
            vol.Schema(  # hs-colors not used
                {
                    vol.Optional(CONF_HUE_ADDRESS): None,
                    vol.Optional(CONF_SATURATION_ADDRESS): None,
                },
                extra=vol.ALLOW_EXTRA,
            ),
            msg=_hs_color_inclusion_msg,
        ),
    )


class NotifySchema(KNXPlatformSchema):
    """Voluptuous schema for KNX notifications."""

    PLATFORM_NAME = SupportedPlatforms.NOTIFY.value

    DEFAULT_NAME = "KNX Notify"

    ENTITY_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Required(KNX_ADDRESS): ga_validator,
        }
    )


class NumberSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX numbers."""

    PLATFORM_NAME = SupportedPlatforms.NUMBER.value

    CONF_MAX = "max"
    CONF_MIN = "min"
    CONF_STEP = "step"
    DEFAULT_NAME = "KNX Number"

    ENTITY_SCHEMA = vol.All(
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_RESPOND_TO_READ, default=False): cv.boolean,
                vol.Required(CONF_TYPE): numeric_type_validator,
                vol.Required(KNX_ADDRESS): ga_list_validator,
                vol.Optional(CONF_STATE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_MAX): vol.Coerce(float),
                vol.Optional(CONF_MIN): vol.Coerce(float),
                vol.Optional(CONF_STEP): cv.positive_float,
            }
        ),
        number_limit_sub_validator,
    )


class SceneSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX scenes."""

    PLATFORM_NAME = SupportedPlatforms.SCENE.value

    CONF_SCENE_NUMBER = "scene_number"

    DEFAULT_NAME = "KNX SCENE"
    ENTITY_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Required(KNX_ADDRESS): ga_list_validator,
            vol.Required(CONF_SCENE_NUMBER): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=64)
            ),
        }
    )


class SelectSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX selects."""

    PLATFORM_NAME = SupportedPlatforms.SELECT.value

    CONF_OPTION = "option"
    CONF_OPTIONS = "options"
    CONF_PAYLOAD = "payload"
    CONF_PAYLOAD_LENGTH = "payload_length"
    DEFAULT_NAME = "KNX Select"

    ENTITY_SCHEMA = vol.All(
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_SYNC_STATE, default=True): sync_state_validator,
                vol.Optional(CONF_RESPOND_TO_READ, default=False): cv.boolean,
                vol.Required(CONF_PAYLOAD_LENGTH): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=14)
                ),
                vol.Required(CONF_OPTIONS): [
                    {
                        vol.Required(CONF_OPTION): vol.Coerce(str),
                        vol.Required(CONF_PAYLOAD): cv.positive_int,
                    }
                ],
                vol.Required(KNX_ADDRESS): ga_list_validator,
                vol.Optional(CONF_STATE_ADDRESS): ga_list_validator,
            }
        ),
        select_options_sub_validator,
    )


class SensorSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX sensors."""

    PLATFORM_NAME = SupportedPlatforms.SENSOR.value

    CONF_ALWAYS_CALLBACK = "always_callback"
    CONF_STATE_ADDRESS = CONF_STATE_ADDRESS
    CONF_SYNC_STATE = CONF_SYNC_STATE
    DEFAULT_NAME = "KNX Sensor"

    ENTITY_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_SYNC_STATE, default=True): sync_state_validator,
            vol.Optional(CONF_ALWAYS_CALLBACK, default=False): cv.boolean,
            vol.Optional(CONF_STATE_CLASS): STATE_CLASSES_SCHEMA,
            vol.Required(CONF_TYPE): sensor_type_validator,
            vol.Required(CONF_STATE_ADDRESS): ga_list_validator,
        }
    )


class SwitchSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX switches."""

    PLATFORM_NAME = SupportedPlatforms.SWITCH.value

    CONF_INVERT = CONF_INVERT
    CONF_STATE_ADDRESS = CONF_STATE_ADDRESS

    DEFAULT_NAME = "KNX Switch"
    ENTITY_SCHEMA = vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Optional(CONF_INVERT, default=False): cv.boolean,
            vol.Optional(CONF_RESPOND_TO_READ, default=False): cv.boolean,
            vol.Required(KNX_ADDRESS): ga_list_validator,
            vol.Optional(CONF_STATE_ADDRESS): ga_list_validator,
        }
    )


class WeatherSchema(KNXPlatformSchema):
    """Voluptuous schema for KNX weather station."""

    PLATFORM_NAME = SupportedPlatforms.WEATHER.value

    CONF_SYNC_STATE = CONF_SYNC_STATE
    CONF_XKNX_TEMPERATURE_ADDRESS = "address_temperature"
    CONF_XKNX_BRIGHTNESS_SOUTH_ADDRESS = "address_brightness_south"
    CONF_XKNX_BRIGHTNESS_EAST_ADDRESS = "address_brightness_east"
    CONF_XKNX_BRIGHTNESS_WEST_ADDRESS = "address_brightness_west"
    CONF_XKNX_BRIGHTNESS_NORTH_ADDRESS = "address_brightness_north"
    CONF_XKNX_WIND_SPEED_ADDRESS = "address_wind_speed"
    CONF_XKNX_WIND_BEARING_ADDRESS = "address_wind_bearing"
    CONF_XKNX_RAIN_ALARM_ADDRESS = "address_rain_alarm"
    CONF_XKNX_FROST_ALARM_ADDRESS = "address_frost_alarm"
    CONF_XKNX_WIND_ALARM_ADDRESS = "address_wind_alarm"
    CONF_XKNX_DAY_NIGHT_ADDRESS = "address_day_night"
    CONF_XKNX_AIR_PRESSURE_ADDRESS = "address_air_pressure"
    CONF_XKNX_HUMIDITY_ADDRESS = "address_humidity"

    DEFAULT_NAME = "KNX Weather Station"

    ENTITY_SCHEMA = vol.All(
        # deprecated since 2021.6
        cv.deprecated("create_sensors"),
        vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_SYNC_STATE, default=True): sync_state_validator,
                vol.Required(CONF_XKNX_TEMPERATURE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_BRIGHTNESS_SOUTH_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_BRIGHTNESS_EAST_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_BRIGHTNESS_WEST_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_BRIGHTNESS_NORTH_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_WIND_SPEED_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_WIND_BEARING_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_RAIN_ALARM_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_FROST_ALARM_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_WIND_ALARM_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_DAY_NIGHT_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_AIR_PRESSURE_ADDRESS): ga_list_validator,
                vol.Optional(CONF_XKNX_HUMIDITY_ADDRESS): ga_list_validator,
            }
        ),
    )
