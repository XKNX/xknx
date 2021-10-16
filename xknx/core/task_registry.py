"""Manages global tasks."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Generator, Union

from xknx.core import XknxConnectionState

AsyncCallbackType = Union[Generator[Any, None, Any], Awaitable]

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.log")


class Task:
    """Handles a given task."""

    def __init__(
        self,
        name: str,
        task: AsyncCallbackType,
        restart_after_reconnect: bool = False,
    ) -> None:
        """Initialize Task class."""
        self.name = name
        self.task = task
        self.restart_after_reconnect = restart_after_reconnect
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Start a task."""
        self._task = asyncio.create_task(self.task, name=self.name)

    def __await__(self) -> Generator[None, None, None]:
        """Wait for task to be finished."""
        if self._task:
            yield from self._task

    def cancel(self) -> None:
        """Cancel a task."""
        if self._task:
            self._task.cancel()
            self._task = None

    def connection_lost(self) -> None:
        """Cancel a task if connection was lost and the task should be cancelled if no connection is established."""
        if self.restart_after_reconnect and self._task:
            logger.debug("Stopping task %s because of connection loss.", self.name)
            self.cancel()

    def reconnected(self) -> None:
        """Restart when reconnected to bus."""
        if self.restart_after_reconnect and not self._task:
            logger.debug(
                "Restarting task %s as the connection to the bus was reestablished.",
                self.name,
            )
            self.start()


class TaskRegistry:
    """Manages async tasks in XKNX."""

    def __init__(self, xknx: XKNX) -> None:
        """Initialize TaskRegistry class."""
        self.xknx = xknx
        self.tasks: list[Task] = []

    def register(
        self,
        name: str,
        task: AsyncCallbackType,
        track_task: bool = True,
        restart_after_reconnect: bool = False,
    ) -> Task:
        """Register new task."""
        self.unregister(name)

        _task: Task = Task(
            name=name, task=task, restart_after_reconnect=restart_after_reconnect
        )

        if track_task:
            self.tasks.append(_task)

        return _task

    def unregister(self, name: str) -> None:
        """Unregister task."""
        for task in self.tasks:
            if task.name == name:
                task.cancel()
                self.tasks.remove(task)

    def start(self) -> None:
        """Start task registry."""
        self.xknx.connection_manager.register_connection_state_changed_cb(
            self.connection_state_changed_cb
        )

    def stop(self) -> None:
        """Stop task registry and cancel all tasks."""
        self.xknx.connection_manager.unregister_connection_state_changed_cb(
            self.connection_state_changed_cb
        )

        for task in self.tasks:
            task.cancel()

        self.tasks = []

    async def block_till_done(self) -> None:
        """Await all tracked tasks."""
        for task in self.tasks:
            await task

    async def connection_state_changed_cb(self, state: XknxConnectionState) -> None:
        """Handle connection state changes."""
        for task in self.tasks:
            if state == XknxConnectionState.CONNECTED:
                task.reconnected()
            else:
                task.connection_lost()
