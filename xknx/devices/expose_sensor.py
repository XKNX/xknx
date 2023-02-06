"""
Module for exposing a (virtual) sensor to KNX bus.

It provides functionality for

* push local state changes to KNX bus
* KNX devices may read local values via GROUP READ.

(A typical example for using this class is the outside temperature
read from e.g. an internet serviceand exposed to the KNX bus.
KNX devices may show this value within their display.)
"""
from __future__ import annotations

import asyncio
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from xknx.core import Task
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
        respond_to_read: bool = True,
        value_type: int | str | None = None,
        cooldown: float = 0,
        device_updated_cb: DeviceCallbackType[ExposeSensor] | None = None,
    ):
        """Initialize Sensor class."""
        super().__init__(xknx, name, device_updated_cb)
        self.cooldown = cooldown
        self.respond_to_read = respond_to_read
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
        self._cooldown_latest_value: Any | None = None
        self._cooldown_task: Task | None = None
        self._cooldown_task_name = f"expose_sensor.cooldown_{id(self)}"

    async def after_update(self) -> None:
        """Call after state was updated."""
        self._cooldown_latest_value = self.sensor_value.value
        await super().after_update()

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    def _iter_tasks(self) -> Iterator[Task | None]:
        """Iterate the device tasks."""
        yield self._cooldown_task

    async def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.sensor_value.process(telegram)

    async def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GROUP READ telegram."""
        if not self.respond_to_read:
            return
        if self._cooldown_latest_value is not None:
            await self.sensor_value.set(self._cooldown_latest_value, response=True)
            return
        await self.sensor_value.respond()

    async def set(self, value: Any) -> None:
        """Set new value."""
        if self.cooldown:
            self._cooldown_latest_value = value
            if self._cooldown_task is not None and not self._cooldown_task.done():
                return
            self._cooldown_task = self.xknx.task_registry.register(
                name=self._cooldown_task_name,
                async_func=self._cooldown_wait,
            ).start()
        await self.sensor_value.set(value)

    async def _cooldown_wait(self) -> None:
        """Send value after cooldown if it differs from last processed value."""
        while True:
            await asyncio.sleep(self.cooldown)
            if self.sensor_value.value == self._cooldown_latest_value:
                break
            await self.sensor_value.set(self._cooldown_latest_value)  # type: ignore[arg-type]

    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def resolve_state(self) -> Any:
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<ExposeSensor name="{self.name}" '
            f"sensor={self.sensor_value.group_addr_str()} "
            f"value={repr(self.sensor_value.value)} "
            f'unit="{self.unit_of_measurement()}"/>'
        )
