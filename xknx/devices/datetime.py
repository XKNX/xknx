"""
Module for broadcasting date/time to the KNX bus.

DateTime is a virtual/pseudo device, optionally
broadcasting localtime periodically.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from functools import partial
import logging
import time
from typing import TYPE_CHECKING

from xknx.core import Task
from xknx.remote_value import GroupAddressesType, RemoteValueDateTime

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


BROADCAST_MINUTES = 60


class DateTime(Device):
    """Class for virtual date/time device."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        broadcast_type: str = "TIME",
        localtime: bool = True,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        respond_to_read: bool = False,
        sync_state: bool | int | float | str = True,
        device_updated_cb: DeviceCallbackType[DateTime] | None = None,
    ):
        """Initialize DateTime class."""
        super().__init__(xknx, name, device_updated_cb)
        self.localtime = localtime
        if localtime and group_address_state is not None:
            logger.warning(
                "State address invalid in DateTime device when using `localtime=True`. Ignoring `group_address_state=%s` argument.",
                group_address_state,
            )
            # state address invalid for localtime - therefore sync_state doesn't apply for localtime
            group_address_state = None
        self.respond_to_read = respond_to_read
        self._broadcast_type = broadcast_type.upper()
        self.remote_value = RemoteValueDateTime(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            value_type=broadcast_type,
            device_name=name,
            after_update_cb=self.after_update,
        )
        self._broadcast_task: Task | None = None

    def _iter_remote_values(self) -> Iterator[RemoteValueDateTime]:
        """Iterate the devices RemoteValue classes."""
        yield self.remote_value

    def async_start_tasks(self) -> None:
        """Create an asyncio.Task for broadcasting local time periodically if `localtime` is set."""
        if not self.localtime:
            return None

        async def broadcast_loop(self: DateTime, minutes: int) -> None:
            """Endless loop for broadcasting local time."""
            while True:
                await self.broadcast_localtime()
                await asyncio.sleep(minutes * 60)

        self._broadcast_task = self.xknx.task_registry.register(
            name=f"datetime.broadcast_{id(self)}",
            async_func=partial(broadcast_loop, self, BROADCAST_MINUTES),
            restart_after_reconnect=True,
        ).start()

    def async_remove_tasks(self) -> None:
        """Stop background tasks of device."""
        if self._broadcast_task is not None:
            self.xknx.task_registry.unregister(self._broadcast_task.name)
            self._broadcast_task = None

    async def broadcast_localtime(self, response: bool = False) -> None:
        """Broadcast the local time to KNX bus."""
        self.remote_value.set(time.localtime(), response=response)

    async def set(self, struct_time: time.struct_time) -> None:
        """Set time and send to KNX bus."""
        self.remote_value.set(struct_time)

    async def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        self.remote_value.process(telegram)

    async def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GROUP READ telegram."""
        if self.localtime:
            await self.broadcast_localtime(True)
        elif (
            self.respond_to_read
            and telegram.destination_address == self.remote_value.group_address
        ):
            self.remote_value.respond()

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read state of device from KNX bus. Used here to broadcast time to KNX bus."""
        if self.localtime:
            await self.broadcast_localtime(response=False)
        else:
            await super().sync(wait_for_result)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<DateTime name="{self.name}" '
            f"remote_value={self.remote_value.group_addr_str()} "
            f'broadcast_type="{self._broadcast_type}" />'
        )
