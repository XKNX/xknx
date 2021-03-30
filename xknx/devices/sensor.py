"""
Module for managing a sensor via KNX.

It provides functionality for

* reading the current state from KNX bus.
* watching for state updates from KNX bus.
"""
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional, Union

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueControl,
    RemoteValueSensor,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class Sensor(Device):
    """Class for managing a sensor."""

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address_state: Optional[GroupAddressesType] = None,
        sync_state: bool = True,
        always_callback: bool = False,
        value_type: Optional[Union[int, str]] = None,
        ha_value_template: Any = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize Sensor class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.sensor_value: Union[RemoteValueControl, RemoteValueSensor]
        if isinstance(value_type, str) and value_type in [
            "stepwise_dimming",
            "stepwise_blinds",
            "startstop_dimming",
            "startstop_blinds",
        ]:
            self.sensor_value = RemoteValueControl(
                xknx,
                group_address_state=group_address_state,
                sync_state=sync_state,
                value_type=value_type,
                device_name=self.name,
                after_update_cb=self.after_update,
            )
        else:
            self.sensor_value = RemoteValueSensor(
                xknx,
                group_address_state=group_address_state,
                sync_state=sync_state,
                value_type=value_type,
                device_name=self.name,
                after_update_cb=self.after_update,
            )
        self.always_callback = always_callback
        self.ha_value_template = ha_value_template

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    @property
    def unique_id(self) -> Optional[str]:
        """Return unique id for this device."""
        return f"{self.sensor_value.group_address_state}"

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Dict[str, Any]) -> "Sensor":
        """Initialize object from configuration structure."""
        group_address_state = config.get("group_address_state")
        sync_state = config.get("sync_state", True)
        always_callback = config.get("always_callback", False)
        value_type = config.get("value_type")

        return cls(
            xknx,
            name,
            group_address_state=group_address_state,
            sync_state=sync_state,
            always_callback=always_callback,
            value_type=value_type,
        )

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.sensor_value.process(telegram, always_callback=self.always_callback)

    async def process_group_response(self, telegram: "Telegram") -> None:
        """Process incoming GroupValueResponse telegrams."""
        await self.sensor_value.process(telegram)

    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def ha_device_class(self) -> Optional[str]:
        """Return the home assistant device class as string."""
        return self.sensor_value.ha_device_class

    def resolve_state(self) -> Optional[Any]:
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<Sensor name="{}" ' 'sensor="{}" value="{}" unit="{}"/>'.format(
            self.name,
            self.sensor_value.group_addr_str(),
            self.resolve_state(),
            self.unit_of_measurement(),
        )
