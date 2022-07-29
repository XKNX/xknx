"""
Module for managing a binary sensor.

A binary sensor can be:
* A switch in the wall (as in the thing you press to switch on the light)
* A motion detector
* A reed sensor for detecting of a window/door is opened or closed.

A BinarySensor may also have Actions attached which are executed after state was changed.
"""
from __future__ import annotations

import asyncio
from collections.abc import Iterator
from functools import partial
import time
from typing import TYPE_CHECKING, cast

from xknx.core import Task
from xknx.remote_value import GroupAddressesType, RemoteValueSwitch

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class BinarySensor(Device):
    """Class for binary sensor."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_state: GroupAddressesType = None,
        invert: bool = False,
        sync_state: bool | int | float | str = True,
        ignore_internal_state: bool = False,
        reset_after: float | None = None,
        context_timeout: float | None = None,
        device_updated_cb: DeviceCallbackType[BinarySensor] | None = None,
    ):
        """Initialize BinarySensor class."""
        super().__init__(xknx, name, device_updated_cb)

        self.ignore_internal_state = ignore_internal_state or bool(context_timeout)
        self.reset_after = reset_after
        self.state: bool | None = None

        self._context_timeout = context_timeout
        self._count_set_on = 0
        self._count_set_off = 0
        self._last_set: float | None = None
        self._reset_task_name = f"binary_sensor.reset_{id(self)}"
        self._context_task_name = f"binary_sensor.context_{id(self)}"
        self._reset_task: Task | None = None
        self._context_task: Task | None = None

        self.remote_value = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_state,
            invert=invert,
            sync_state=sync_state,
            device_name=self.name,
            # after_update called internally
            after_update_cb=self._state_from_remote_value,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueSwitch]:
        """Iterate the devices RemoteValue classes."""
        yield self.remote_value

    def _iter_tasks(self) -> Iterator[Task | None]:
        """Iterate the device tasks."""
        yield self._context_task
        yield self._reset_task

    @property
    def last_telegram(self) -> Telegram | None:
        """Return the last telegram received from the RemoteValue."""
        return self.remote_value.telegram

    async def _state_from_remote_value(self) -> None:
        """Update the internal state from RemoteValue (Callback)."""
        if self.remote_value.value is not None:
            await self._set_internal_state(self.remote_value.value)

    async def _set_internal_state(self, state: bool) -> None:
        """Set the internal state of the device. If state was changed after_update hooks and connected Actions are executed."""
        if state != self.state or self.ignore_internal_state:
            self.state = state

            if self.ignore_internal_state and self._context_timeout:
                self.bump_and_get_counter(state)
                self._context_task = self.xknx.task_registry.register(
                    name=self._context_task_name,
                    async_func=partial(self._counter_task, self._context_timeout),
                ).start()
            else:
                await self.after_update()

    async def _counter_task(self, wait_seconds: float) -> None:
        """Trigger after 1 second to prevent double triggers."""
        await asyncio.sleep(wait_seconds)
        await self.after_update()

        self._count_set_on = 0
        self._count_set_off = 0
        await self.after_update()

    @property
    def counter(self) -> int | None:
        """Return current counter for sensor."""
        if self._context_timeout:
            return self._count_set_on if self.state else self._count_set_off
        return None

    def bump_and_get_counter(self, state: bool) -> int:
        """Bump counter and return the number of times a state was set to the same value within CONTEXT_TIMEOUT."""

        def within_same_context() -> bool:
            """Check if state change was within same context (e.g. 'Button was pressed twice')."""
            if self._last_set is None:
                self._last_set = time.time()
                return False
            new_set_time = time.time()
            time_diff = new_set_time - self._last_set
            self._last_set = new_set_time
            return time_diff < cast(float, self._context_timeout)

        if within_same_context():
            if state:
                self._count_set_on = self._count_set_on + 1
                return self._count_set_on
            self._count_set_off = self._count_set_off + 1
            return self._count_set_off

        if state:
            self._count_set_on = 1
            self._count_set_off = 0
        else:
            self._count_set_on = 0
            self._count_set_off = 1
        return 1

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        if await self.remote_value.process(telegram, always_callback=True):
            self._process_reset_after()

    async def process_group_response(self, telegram: "Telegram") -> None:
        """Process incoming GroupValueResponse telegrams."""
        if await self.remote_value.process(telegram, always_callback=False):
            self._process_reset_after()

    def _process_reset_after(self) -> None:
        """Create Task for resetting state if 'reset_after' is configured."""
        if self.reset_after is not None and self.state:
            self._reset_task = self.xknx.task_registry.register(
                name=self._reset_task_name,
                async_func=partial(self._reset_state, self.reset_after),
                track_task=True,
            ).start()

    async def _reset_state(self, wait_seconds: float) -> None:
        await asyncio.sleep(wait_seconds)
        await self._set_internal_state(False)

    def is_on(self) -> bool:
        """Return if binary sensor is 'on'."""
        return bool(self.state)

    def is_off(self) -> bool:
        """Return if binary sensor is 'off'."""
        return not self.state

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<BinarySensor name="{self.name}" '
            f"remote_value={self.remote_value.group_addr_str()} "
            f"state={self.state.__repr__()} />"
        )
