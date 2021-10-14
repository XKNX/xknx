"""Exposures to KNX bus."""
from __future__ import annotations

from collections.abc import Callable

from xknx import XKNX
from xknx.devices import DateTime, ExposeSensor
from xknx.dpt import DPTNumeric
from xknx.remote_value import RemoteValueSensor

from homeassistant.const import (
    CONF_ENTITY_ID,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.typing import ConfigType, StateType

from .const import KNX_ADDRESS
from .schema import ExposeSchema


@callback
def create_knx_exposure(
    hass: HomeAssistant, xknx: XKNX, config: ConfigType
) -> KNXExposeSensor | KNXExposeTime:
    """Create exposures from config."""
    address = config[KNX_ADDRESS]
    expose_type = config[ExposeSchema.CONF_XKNX_EXPOSE_TYPE]
    attribute = config.get(ExposeSchema.CONF_XKNX_EXPOSE_ATTRIBUTE)
    default = config.get(ExposeSchema.CONF_XKNX_EXPOSE_DEFAULT)

    exposure: KNXExposeSensor | KNXExposeTime
    if (
        isinstance(expose_type, str)
        and expose_type.lower() in ExposeSchema.EXPOSE_TIME_TYPES
    ):
        exposure = KNXExposeTime(xknx, expose_type, address)
    else:
        entity_id = config[CONF_ENTITY_ID]
        exposure = KNXExposeSensor(
            hass,
            xknx,
            expose_type,
            entity_id,
            attribute,
            default,
            address,
        )
    return exposure


class KNXExposeSensor:
    """Object to Expose Home Assistant entity to KNX bus."""

    def __init__(
        self,
        hass: HomeAssistant,
        xknx: XKNX,
        expose_type: int | str,
        entity_id: str,
        attribute: str | None,
        default: StateType,
        address: str,
    ) -> None:
        """Initialize of Expose class."""
        self.hass = hass
        self.xknx = xknx
        self.type = expose_type
        self.entity_id = entity_id
        self.expose_attribute = attribute
        self.expose_default = default
        self.address = address
        self._remove_listener: Callable[[], None] | None = None
        self.device: ExposeSensor = self.async_register()
        self._init_expose_state()

    @callback
    def async_register(self) -> ExposeSensor:
        """Register listener."""
        if self.expose_attribute is not None:
            _name = self.entity_id + "__" + self.expose_attribute
        else:
            _name = self.entity_id
        device = ExposeSensor(
            self.xknx,
            name=_name,
            group_address=self.address,
            value_type=self.type,
        )
        self._remove_listener = async_track_state_change_event(
            self.hass, [self.entity_id], self._async_entity_changed
        )
        return device

    @callback
    def _init_expose_state(self) -> None:
        """Initialize state of the exposure."""
        init_state = self.hass.states.get(self.entity_id)
        state_value = self._get_expose_value(init_state)
        self.device.sensor_value.value = state_value

    @callback
    def shutdown(self) -> None:
        """Prepare for deletion."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
        self.device.shutdown()

    def _get_expose_value(self, state: State | None) -> StateType:
        """Extract value from state."""
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            value = self.expose_default
        else:
            value = (
                state.state
                if self.expose_attribute is None
                else state.attributes.get(self.expose_attribute, self.expose_default)
            )
        if self.type == "binary":
            if value in (1, STATE_ON, "True"):
                return True
            if value in (0, STATE_OFF, "False"):
                return False
        if (
            value is not None
            and isinstance(self.device.sensor_value, RemoteValueSensor)
            and issubclass(self.device.sensor_value.dpt_class, DPTNumeric)
        ):
            return float(value)
        return value

    async def _async_entity_changed(self, event: Event) -> None:
        """Handle entity change."""
        new_state = event.data.get("new_state")
        new_value = self._get_expose_value(new_state)
        if new_value is None:
            return
        old_state = event.data.get("old_state")
        # don't use default value for comparison on first state change (old_state is None)
        old_value = self._get_expose_value(old_state) if old_state is not None else None
        # don't send same value sequentially
        if new_value != old_value:
            await self._async_set_knx_value(new_value)

    async def _async_set_knx_value(self, value: StateType) -> None:
        """Set new value on xknx ExposeSensor."""
        if value is None:
            return
        await self.device.set(value)


class KNXExposeTime:
    """Object to Expose Time/Date object to KNX bus."""

    def __init__(self, xknx: XKNX, expose_type: str, address: str) -> None:
        """Initialize of Expose class."""
        self.xknx = xknx
        self.expose_type = expose_type
        self.address = address
        self.device: DateTime = self.async_register()

    @callback
    def async_register(self) -> DateTime:
        """Register listener."""
        return DateTime(
            self.xknx,
            name=self.expose_type.capitalize(),
            broadcast_type=self.expose_type.upper(),
            localtime=True,
            group_address=self.address,
        )

    @callback
    def shutdown(self) -> None:
        """Prepare for deletion."""
        self.device.shutdown()
