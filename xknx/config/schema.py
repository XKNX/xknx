"""Config validation."""
import voluptuous as vol

from .config_validation import (
    boolean,
    ensure_group_address,
    ensure_list,
    positive_int,
    string,
)

CONF_ADDRESS = "address"
CONF_STATE_ADDRESS = "state_address"
CONF_SWITCH = "switch"


class RemoteValueSchema:
    """Schema validation for remote value configuration."""

    CONF_STATE_UPDATE = "state_update"
    CONF_PASSIVE_GROUP_ADDRESSES = "passive_state_addresses"

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


class SwitchSchema:
    """Schema validation for switches."""

    SCHEMA = BaseDeviceSchema.SCHEMA.extend(
        {
            vol.Required(CONF_SWITCH): RemoteValueSchema.SCHEMA.extend(
                {vol.Required(CONF_ADDRESS): ensure_group_address}
            )
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
