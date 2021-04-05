"""
Module for exposing a (virtual) sensor to KNX bus.

It provides functionality for

* push local state changes to KNX bus
* KNX devices may read local values via GROUP READ.

(A typical example for using this class is the outside temperature
read from an internet service (e.g. Yahoo weather) and exposed to
ths KNX bus. KNX sensors may show this outside temperature within their
LCD display.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueSensor,
    RemoteValueSwitch,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class ExposeSensor(Device):
    """Class for managing a sensor."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType | None = None,
        value_type: int | str | None = None,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize Sensor class."""
        super().__init__(xknx, name, device_updated_cb)

        self.sensor_value: RemoteValueSensor | RemoteValueSwitch
        if value_type == "binary":
            self.sensor_value = RemoteValueSwitch(
                xknx,
                group_address=group_address,
                sync_state=False,
                device_name=self.name,
                after_update_cb=self.after_update,
            )
        else:
            self.sensor_value = RemoteValueSensor(
                xknx,
                group_address=group_address,
                sync_state=False,
                device_name=self.name,
                after_update_cb=self.after_update,
                value_type=value_type,
            )

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.sensor_value.process(telegram)

    async def process_group_read(self, telegram: "Telegram") -> None:
        """Process incoming GROUP READ telegram."""
        await self.sensor_value.respond()

    async def set(self, value: Any) -> None:
        """Set new value."""
        await self.sensor_value.set(value)

    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def resolve_state(self) -> Any:
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<ExposeSensor name="{}" ' 'sensor="{}" value="{}" unit="{}"/>'.format(
            self.name,
            self.sensor_value.group_addr_str(),
            self.resolve_state(),
            self.unit_of_measurement(),
        )
