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
from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueSensor,
    RemoteValueSwitch,
)
from xknx.telegram import TelegramDirection
from xknx.typing import DPTParsable

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
        group_address: GroupAddressesType = None,
        respond_to_read: bool = True,
        value_type: DPTParsable | type[DPTBase] | None = None,
        cooldown: float = 0,
        periodic_send: float = 0,
        device_updated_cb: DeviceCallbackType[ExposeSensor] | None = None,
    ) -> None:
        """
        Initialize ExposeSensor class.

        Args:
        xknx: XKNX instance to use for communication.
        name: Name of the device.
        group_address: KNX group address to send the value to.
        respond_to_read: If True, respond to GroupValueRead telegrams with the
            current value.
        value_type: DPT type or identifier used to encode the sensor value.
        cooldown: Minimum time in seconds between sending values to the KNX
            bus. If multiple updates occur during this period, only the last
            value is sent when the cooldown ends. ``0`` (default) disables cooldown.
        periodic_send: Interval in seconds for automatically re-sending the
            current value. A value of ``0`` (default) disables periodic sending.
        device_updated_cb: Callback invoked when the device has been
            updated.

        """
        super().__init__(xknx, name, device_updated_cb)
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
        self.cooldown = cooldown
        # the next payload to be sent after cooldown or the last sent payload
        self._payload_after_cooldown: DPTArray | DPTBinary | None = None
        self._cooldown_task: Task | None = None
        self._cooldown_task_name = f"expose_sensor.cooldown_{id(self)}"

        self._periodic_send_time = periodic_send
        self._periodic_send_task: Task | None = None

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    def async_start_tasks(self) -> None:
        """Start async background tasks of device."""
        if self._periodic_send_time > 0:
            self._periodic_send_task = self.xknx.task_registry.register(
                name=f"expose_sensor.periodic_send_{id(self)}",
                target=self._periodic_send_loop,
                restart_after_reconnect=True,
            ).start()

    def async_remove_tasks(self) -> None:
        """Remove async tasks of device."""
        if self._cooldown_task is not None:
            self.xknx.task_registry.unregister(self._cooldown_task.name)
            self._cooldown_task = None
        if self._periodic_send_task is not None:
            self.xknx.task_registry.unregister(self._periodic_send_task.name)
            self._periodic_send_task = None

    def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        self.sensor_value.process(telegram)
        # reset periodic send timer
        if (
            telegram.direction is TelegramDirection.OUTGOING
            and self._periodic_send_task is not None
        ):
            self._periodic_send_task.cancel()
            self._periodic_send_task.start()

    def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GROUP READ telegram."""
        if not self.respond_to_read:
            return
        if self._payload_after_cooldown is not None:
            # reading shall not be affected by cooldown, but restart the timer
            self.sensor_value.send_raw(self._payload_after_cooldown, response=True)
            self._restart_cooldown()
            return
        self.sensor_value.respond()

    async def set(self, value: Any, skip_unchanged: bool = False) -> None:
        """
        Set new value.

        Set `skip_unchanged` to skip sending when the encoded payload matches the last one.
        """
        payload = self.sensor_value.to_knx(value)
        if skip_unchanged and self._payload_after_cooldown == payload:
            return
        self._payload_after_cooldown = payload

        if self.cooldown:
            if self._cooldown_task is not None and not self._cooldown_task.done():
                return
            self._cooldown_task = self.xknx.task_registry.register(
                name=self._cooldown_task_name,
                target=self._cooldown_wait,
            ).start()
        self.sensor_value.send_raw(payload)

    async def _cooldown_wait(self) -> None:
        """Send value after cooldown if it differs from last processed value."""
        while True:
            await asyncio.sleep(self.cooldown)
            if self.sensor_value.last_payload == self._payload_after_cooldown:
                break
            self.sensor_value.send_raw(self._payload_after_cooldown)  # type: ignore[arg-type]

    def _restart_cooldown(self) -> None:
        """Reset cooldown task."""
        if not self.cooldown:
            return
        if self._cooldown_task is not None and not self._cooldown_task.done():
            self._cooldown_task.cancel()
            self._cooldown_task.start()
            return
        self._cooldown_task = self.xknx.task_registry.register(
            name=self._cooldown_task_name,
            target=self._cooldown_wait,
        ).start()

    async def _periodic_send_loop(self) -> None:
        """Endless loop for periodic sending of sensor value."""
        while True:
            await asyncio.sleep(self._periodic_send_time)
            if self._payload_after_cooldown is not None:
                self.sensor_value.send_raw(self._payload_after_cooldown)
                self._restart_cooldown()

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
            f"value={self.sensor_value.value!r} "
            f'unit="{self.unit_of_measurement()}"/>'
        )
