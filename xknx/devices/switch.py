"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from functools import partial
import logging
from typing import TYPE_CHECKING

from xknx.core import Task
from xknx.remote_value import GroupAddressesType, RemoteValueSwitch

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Switch(Device):
    """Class for managing a switch."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        respond_to_read: bool = False,
        sync_state: bool | int | float | str = True,
        invert: bool = False,
        reset_after: float | None = None,
        device_updated_cb: DeviceCallbackType[Switch] | None = None,
    ) -> None:
        """Initialize Switch class."""
        super().__init__(xknx, name, device_updated_cb)

        self.reset_after = reset_after
        self._reset_task: Task | None = None
        self.respond_to_read = respond_to_read
        self.switch = RemoteValueSwitch(
            xknx,
            group_address,
            group_address_state,
            sync_state=sync_state,
            invert=invert,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueSwitch]:
        """Iterate the devices RemoteValue classes."""
        yield self.switch

    def async_remove_tasks(self) -> None:
        """Remove async tasks of device."""
        if self._reset_task is not None:
            self._reset_task.cancel()
            self._reset_task = None

    @property
    def state(self) -> bool | None:
        """Return the current switch state of the device."""
        return self.switch.value

    async def set_on(self) -> None:
        """Switch on switch."""
        self.switch.on()

    async def set_off(self) -> None:
        """Switch off switch."""
        self.switch.off()

    def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        if self.switch.process(telegram):
            if self.reset_after is not None and self.switch.value:
                self._reset_task = self.xknx.task_registry.register(
                    name=f"switch.reset_{id(self)}",
                    async_func=partial(self._reset_state, self.reset_after),
                    track_task=True,
                ).start()

    def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GroupValueResponse telegrams."""
        if (
            self.respond_to_read
            and telegram.destination_address == self.switch.group_address
        ):
            self.switch.respond()

    async def _reset_state(self, wait_seconds: float) -> None:
        await asyncio.sleep(wait_seconds)
        await self.set_off()

    def __str__(self) -> str:
        """Return object as readable string."""
        return f'<Switch name="{self.name}" switch={self.switch.group_addr_str()} />'
