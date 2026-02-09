"""Unit test for task registry."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.core.task_registry import Task

from ..conftest import EventLoopClockAdvancer


class TestTaskRegistry:
    """Test class for task registry."""

    @pytest.mark.parametrize("target", ["async", "sync"])
    async def test_start_task(self, target: str) -> None:
        """Test start_task."""
        xknx = XKNX()
        mock = AsyncMock() if target == "async" else Mock()

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=mock,
            )
        )
        assert len(xknx.task_registry.tasks) == 1

        assert not task.done()
        assert mock.call_count == 0
        if target == "async":
            assert mock.await_count == 0

        await xknx.task_registry.block_till_done()
        assert task.done()
        assert mock.call_count == 1
        if target == "async":
            assert mock.await_count == 1

    async def test_unregister(self) -> None:
        """Test unregister after starting task."""
        xknx = XKNX()
        mock = Mock()

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=mock,
            )
        )
        assert len(xknx.task_registry.tasks) == 1
        xknx.task_registry.unregister(task)
        assert len(xknx.task_registry.tasks) == 0
        assert task.done()

        assert mock.call_count == 0

    #
    # TEST START/STOP
    #
    async def test_stop(self) -> None:
        """Test stop."""
        xknx = XKNX()

        async def callback() -> None:
            """Reset tasks."""
            await asyncio.sleep(1)
            raise AssertionError("Task should have been cancelled")

        task = Task(
            name="test",
            target=callback,
        )
        xknx.task_registry.start_task(task)

        assert len(xknx.task_registry.tasks) == 1
        xknx.task_registry.stop()
        assert len(xknx.task_registry.tasks) == 0
        assert task.done()

    #
    # TEST CONNECTION HANDLING
    #
    async def test_reconnect_handling(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test reconnect handling."""

        xknx = XKNX()
        xknx.task_registry.start()
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 1
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)

        test = 0

        async def callback() -> None:
            """Reset tasks."""
            nonlocal test
            try:
                while True:
                    await asyncio.sleep(100)
                    test += 1
            except asyncio.CancelledError:
                test -= 1

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=callback,
                restart_after_reconnect=True,
            )
        )
        assert len(xknx.task_registry.tasks) == 1
        assert task._task is not None
        await time_travel(100)
        assert test == 1

        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        await asyncio.sleep(0)  # iterate loop to cancel task
        assert task._task is None
        assert test == 0

        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        assert task._task is not None
        assert test == 0

        await time_travel(100)
        assert test == 1
        assert len(xknx.task_registry.tasks) == 1

        xknx.task_registry.stop()
        assert len(xknx.task_registry.tasks) == 0
        assert task._task is None
        await asyncio.sleep(0)  # iterate loop to cancel task
        assert test == 0
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 0

    async def test_wait_before_start(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test wait_before_start argument."""
        xknx = XKNX()
        mock = AsyncMock()
        wait_time = 5

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=mock,
                wait_before_start=wait_time,
            )
        )

        # Task should not be called immediately
        assert mock.call_count == 0
        assert mock.await_count == 0
        assert not task.done()

        # Task should not be called after half the wait time
        await time_travel(wait_time / 2)
        assert mock.call_count == 0
        assert mock.await_count == 0
        assert not task.done()

        # Task should be called after the full wait time
        await time_travel(wait_time / 2)
        assert mock.call_count == 1
        assert mock.await_count == 1
        assert task.done()

        # run again - verify target can be called again and wait_before_start applies again
        task.start()
        await time_travel(wait_time / 2)
        assert mock.call_count == 1
        await time_travel(wait_time / 2)
        assert mock.call_count == 2
        assert mock.await_count == 2
        assert task.done()

    async def test_wait_for_connection(self) -> None:
        """Test wait_for_connection argument."""
        xknx = XKNX()
        mock = Mock()

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=mock,
                wait_for_connection=True,
            )
        )

        # Task should not be called immediately when not connected
        await asyncio.sleep(0)
        assert mock.call_count == 0
        assert not task.done()

        # Task should be called after connection is established
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        await asyncio.sleep(0)
        assert mock.call_count == 1
        assert task.done()

    async def test_repeat_after(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test repeat_after argument."""
        xknx = XKNX()
        mock = Mock()
        repeat_after = 5

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=mock,
                repeat_after=repeat_after,
            )
        )

        await asyncio.sleep(0)
        assert mock.call_count == 1
        assert not task.done()

        await time_travel(repeat_after)
        assert mock.call_count == 2
        assert not task.done()

        await time_travel(repeat_after)
        assert mock.call_count == 3
        assert not task.done()

        task.cancel()
        await asyncio.sleep(0)
        assert task.done()

    async def test_wait_before_start_no_connection_with_restart(
        self, time_travel: EventLoopClockAdvancer
    ) -> None:
        """Test restart_after_reconnect when wait_before_start ends without connection."""
        xknx = XKNX()
        xknx.task_registry.start()
        mock = Mock()
        wait_time = 5

        task = xknx.task_registry.start_task(
            Task(
                name="test",
                target=mock,
                restart_after_reconnect=True,
                wait_before_start=wait_time,
                wait_for_connection=True,
            )
        )

        await time_travel(wait_time)
        await asyncio.sleep(0)
        assert mock.call_count == 0
        assert task.done()

        # restarted when connection is reestablished - wait_before_start should apply again
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        await asyncio.sleep(0)
        assert not task.done()
        assert mock.call_count == 0

        await time_travel(wait_time)
        await asyncio.sleep(0)
        assert mock.call_count == 1
        assert task.done()

    async def test_start_before_register(self) -> None:
        """Test that start() without registration in TaskRegistry raises RuntimeError."""
        task = Task(
            name="test",
            target=Mock(),
        )

        with pytest.raises(RuntimeError, match="Task must be registered before start"):
            task.start()

    async def test_background(self, time_travel: EventLoopClockAdvancer) -> None:
        """Test running background task."""
        test_time = 10

        async def callback() -> None:
            """Do nothing."""
            await asyncio.sleep(test_time)

        xknx = XKNX()
        xknx.task_registry.background(callback())
        assert len(xknx.task_registry._background_task) == 1
        task = next(iter(xknx.task_registry._background_task))
        assert not task.done()

        await time_travel(test_time / 2)
        assert not task.done()
        assert task in xknx.task_registry._background_task

        await time_travel(test_time / 2)
        # after task is finished it should remove itself from the background registry
        assert task.done()
        assert task not in xknx.task_registry._background_task
