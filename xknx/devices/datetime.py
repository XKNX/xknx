"""
Module for broadcasting date/time to the KNX bus.

DateTime is a virtual/pseudo device, optionally
broadcasting localtime periodically.
"""
from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Iterator

from xknx.core import Task
from xknx.remote_value import GroupAddressesType, RemoteValueDateTime

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class DateTime(Device):
    """Class for virtual date/time device."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        broadcast_type: str = "TIME",
        localtime: bool = True,
        group_address: GroupAddressesType | None = None,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize DateTime class."""
        super().__init__(xknx, name, device_updated_cb)
        self.localtime = localtime
        self._broadcast_type = broadcast_type.upper()
        self._remote_value = RemoteValueDateTime(
            xknx,
            group_address=group_address,
            sync_state=False,
            value_type=broadcast_type,
            device_name=name,
            after_update_cb=self.after_update,
        )
        self._broadcast_task: Task | None = self._create_broadcast_task(minutes=60)

    def _iter_remote_values(self) -> Iterator[RemoteValueDateTime]:
        """Iterate the devices RemoteValue classes."""
        yield self._remote_value

    def _iter_tasks(self) -> Iterator[Task | None]:
        """Iterate the device tasks."""
        yield self._broadcast_task

    def _create_broadcast_task(self, minutes: int = 60) -> Task | None:
        """Create an asyncio.Task for broadcasting local time periodically if `localtime` is set."""

        async def broadcast_loop(self: "DateTime", minutes: int) -> None:
            """Endless loop for broadcasting local time."""
            while True:
                await self.broadcast_localtime()
                await asyncio.sleep(minutes * 60)

        if self.localtime:
            task: Task = self.xknx.task_registry.register(
                f"datetime.broadcast_{id(self)}",
                broadcast_loop(self, minutes=minutes),
                restart_after_reconnect=True,
            )
            task.start()
            return task
        return None

    async def broadcast_localtime(self, response: bool = False) -> None:
        """Broadcast the local time to KNX bus."""
        await self._remote_value.set(time.localtime(), response=response)

    async def set(self, struct_time: time.struct_time) -> None:
        """Set time and send to KNX bus."""
        await self._remote_value.set(struct_time)

    async def process_group_read(self, telegram: "Telegram") -> None:
        """Process incoming GROUP READ telegram."""
        if self.localtime:
            await self.broadcast_localtime(True)
        else:
            await self._remote_value.respond()

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read state of device from KNX bus. Used here to broadcast time to KNX bus."""
        if self.localtime:
            await self.broadcast_localtime(response=False)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<DateTime name="{self.name}" '
            f"_remote_value={self._remote_value.group_addr_str()} "
            f'broadcast_type="{self._broadcast_type}" />'
        )
