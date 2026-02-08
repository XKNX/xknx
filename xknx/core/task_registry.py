"""Manages global tasks."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine, Generator
import logging
from typing import TYPE_CHECKING, Any

from xknx.core import XknxConnectionState

AsyncCallbackType = Callable[[], Coroutine[Any, Any, None]]

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.log")


class Task:
    """Handles a given task."""

    __slots__ = (
        "_task",
        "name",
        "restart_after_reconnect",
        "target",
        "wait_before_start",
        "wait_for_connection",
        "xknx",
    )

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        target: AsyncCallbackType | Callable[[], None],
        restart_after_reconnect: bool = False,
        wait_before_start: float = 0,
        wait_for_connection: bool = False,
    ) -> None:
        """
        Initialize a task that can be managed by the TaskRegistry.

        The task execution order is: wait_before_start delay → wait_for_connection (if enabled) → execute target.

        Args:
            xknx: The XKNX instance managing this task.
            name: Unique identifier for the task, used in logging and task management.
            target: The function to execute. Can be async or sync. Sync functions will run in the main
                event loop thread so shall not perform blocking operations.
            restart_after_reconnect: When True, automatically cancels and restarts the task when the
                KNX bus connection is lost and reestablished.
            wait_before_start: Initial delay in seconds before the task begins execution. Applied before
                checking for connection if wait_for_connection is also enabled.
            wait_for_connection: When True, blocks task execution until a KNX bus connection is established.
                The task will wait indefinitely until connected.

        """
        self.xknx = xknx
        self.name = name
        self.target = target
        self.restart_after_reconnect = restart_after_reconnect
        self.wait_before_start = wait_before_start
        self.wait_for_connection = wait_for_connection
        self._task: asyncio.Task[None] | None = None

    def start(self) -> Task:
        """Start a task."""
        self._task = asyncio.create_task(self._start(), name=self.name)
        return self

    async def _start(self) -> None:
        if self.wait_before_start:
            await asyncio.sleep(self.wait_before_start)
        if self.wait_for_connection:
            await self.xknx.connection_manager.connected.wait()
        job = self.target()
        if asyncio.iscoroutine(job):
            await job

    def __await__(self) -> Generator[None, None, None]:
        """Wait for task to be finished."""
        if self._task:
            yield from self._task

    def cancel(self) -> None:
        """Cancel a task."""
        if self._task:
            self._task.cancel()
            self._task = None

    def done(self) -> bool:
        """Return if task is finished."""
        return self._task is None or self._task.done()

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

    __slots__ = ("_background_task", "tasks", "xknx")

    def __init__(self, xknx: XKNX) -> None:
        """Initialize TaskRegistry class."""
        self.xknx = xknx
        self.tasks: list[Task] = []

        self._background_task: set[asyncio.Task[None]] = set()

    def register(
        self,
        name: str,
        target: AsyncCallbackType | Callable[[], None],
        restart_after_reconnect: bool = False,
        wait_before_start: float = 0,
        wait_for_connection: bool = False,
    ) -> Task:
        """Register new task."""
        self.unregister(name)

        _task = Task(
            xknx=self.xknx,
            name=name,
            target=target,
            restart_after_reconnect=restart_after_reconnect,
            wait_before_start=wait_before_start,
            wait_for_connection=wait_for_connection,
        )
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
        await asyncio.gather(*self.tasks)

    def connection_state_changed_cb(self, state: XknxConnectionState) -> None:
        """Handle connection state changes."""
        for task in self.tasks:
            if state == XknxConnectionState.CONNECTED:
                task.reconnected()
            else:
                task.connection_lost()

    def background(self, async_func: Coroutine[Any, Any, None]) -> None:
        """
        Run an async task in the background. Task will not be tracked by the TaskRegistry.

        This is a helper method for keeping references to asyncio tasks to prevent
        them from being garbage collected while they are still running.
        """
        # Add task to the set. This creates a strong reference so it can't be garbage collected.
        task = asyncio.create_task(async_func)
        # To prevent keeping references to finished tasks forever,
        self._background_task.add(task)
        # make each task remove its own reference from the set after
        # completion:
        task.add_done_callback(self._background_task.discard)
