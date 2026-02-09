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
        "repeat_after",
        "restart_after_reconnect",
        "target",
        "wait_before_start",
        "wait_for_connection",
        "xknx",
    )

    def __init__(
        self,
        name: str,
        target: AsyncCallbackType | Callable[[], None],
        *,
        restart_after_reconnect: bool = False,
        wait_before_start: float = 0,
        wait_for_connection: bool = False,
        repeat_after: float | None = None,
    ) -> None:
        """
        Initialize a task that can be managed by the TaskRegistry.

        The task execution order is: wait_before_start delay
        → wait_for_connection (if enabled)
        → execute target
        → repeat_after interval (if enabled).

        Args:
            name: Unique identifier for the task, used in logging and task management.
            target: The function to execute. Can be async or sync. Sync functions will run in the main
                event loop thread so shall not perform blocking operations.
            restart_after_reconnect: When True, automatically cancels and restarts the task when the
                KNX bus connection is lost and reestablished. Wait_before_start and wait_for_connection options
                will apply on each restart.
            wait_before_start: Initial delay in seconds before the task begins execution. Applied before
                checking for connection if wait_for_connection is also enabled.
            wait_for_connection: When True, blocks task execution until a KNX bus connection is established.
                The task will wait indefinitely until connected.
            repeat_after: Interval in seconds to repeat the task execution. If None, the task will run only once.

        """
        self.xknx: XKNX | None = None  # used as flag for registration in TaskRegistry
        self.name = name
        self.target = target
        self.restart_after_reconnect = restart_after_reconnect
        self.wait_before_start = wait_before_start
        self.wait_for_connection = wait_for_connection
        self.repeat_after = repeat_after
        self._task: asyncio.Task[None] | None = None

    def _start(self) -> None:
        """Start a task. Shall be called by TaskRegistry.start_task() to ensure proper registration."""
        if self.xknx is None:
            raise RuntimeError("Task must be registered before start().")
        self._task = asyncio.create_task(self._start_internal(), name=self.name)

    async def _start_internal(self) -> None:
        """Start a task and handle options."""
        while True:
            if self.wait_before_start:
                await asyncio.sleep(self.wait_before_start)
            if self.wait_for_connection:
                assert self.xknx is not None
                if not self.xknx.connection_manager.connected.is_set():
                    if self.restart_after_reconnect:
                        # self.reconnected() will restart the task when connection is
                        # reestablished. This will trigger wait_before_start again.
                        return
                    await self.xknx.connection_manager.connected.wait()

            job = self.target()
            if asyncio.iscoroutine(job):
                await job

            if self.repeat_after is None:
                break
            await asyncio.sleep(self.repeat_after)

    def __await__(self) -> Generator[None, None, None]:
        """Wait for task to be finished."""
        if self._task:
            yield from self._task

    def cancel(self) -> None:
        """Cancel a task."""
        if self._task:
            self._task.cancel()
            self._task = None

    def restart(self) -> None:
        """Restart a task."""
        self.cancel()
        self._start()

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
        if self.restart_after_reconnect:
            logger.debug(
                "Restarting task %s as the connection to the bus was reestablished.",
                self.name,
            )
            self.restart()


class TaskRegistry:
    """Manages async tasks in XKNX."""

    __slots__ = ("_background_task", "tasks", "xknx")

    def __init__(self, xknx: XKNX) -> None:
        """Initialize TaskRegistry class."""
        self.xknx = xknx
        self.tasks: set[Task] = set()

        self._background_task: set[asyncio.Task[None]] = set()

    def start_task(self, task: Task) -> None:
        """Register a task and start it. If it is already running, it will be restarted."""
        self.remove_task(task)
        _task = task
        # set xknx to flag registration and allow starting the task
        _task.xknx = self.xknx
        self.tasks.add(_task)
        # ruff: noqa: SLF001
        _task._start()  # pylint: disable=protected-access

    def remove_task(self, task: Task) -> None:
        """Cancel and unregister task."""
        if task in self.tasks:
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
        self.tasks = set()

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
