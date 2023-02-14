"""Unit test for task registry."""
import asyncio
import sys

from xknx import XKNX
from xknx.core import XknxConnectionState


class TestTaskRegistry:
    """Test class for task registry."""

    #
    # TEST REGISTER/UNREGISTER
    #
    async def test_register(self):
        """Test register."""

        xknx = XKNX()

        async def callback() -> None:
            """Reset tasks."""
            xknx.task_registry.tasks = []

        task = xknx.task_registry.register(
            name="test",
            async_func=callback,
        )
        assert len(xknx.task_registry.tasks) == 1

        task.start()
        assert not task.done()

        await xknx.task_registry.block_till_done()
        assert task.done()
        assert len(xknx.task_registry.tasks) == 0

    async def test_unregister(self):
        """Test unregister after register."""

        xknx = XKNX()

        async def callback() -> None:
            """Do nothing."""

        task = xknx.task_registry.register(
            name="test",
            async_func=callback,
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        xknx.task_registry.unregister(task.name)
        assert len(xknx.task_registry.tasks) == 0
        assert task.done()

    #
    # TEST START/STOP
    #
    async def test_stop(self):
        """Test stop."""

        xknx = XKNX()

        async def callback() -> None:
            """Reset tasks."""
            await asyncio.sleep(100)

        task = xknx.task_registry.register(
            name="test",
            async_func=callback,
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        xknx.task_registry.stop()
        assert len(xknx.task_registry.tasks) == 0

    #
    # TEST CONNECTION HANDLING
    #
    async def test_reconnect_handling(self, time_travel):
        """Test reconnect handling."""

        xknx = XKNX()
        xknx.task_registry.start()
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 1
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        # pylint: disable=attribute-defined-outside-init
        self.test = 0

        async def callback() -> None:
            """Reset tasks."""
            try:
                while True:
                    await asyncio.sleep(100)
                    self.test += 1
            except asyncio.CancelledError:
                self.test -= 1

        task = xknx.task_registry.register(
            name="test", async_func=callback, restart_after_reconnect=True
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        assert task._task is not None
        await time_travel(100)
        assert self.test == 1
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        assert task._task is None
        assert self.test == 0
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        assert task._task is not None
        assert self.test == 0
        await time_travel(100)
        assert self.test == 1
        assert len(xknx.task_registry.tasks) == 1

        xknx.task_registry.stop()
        assert len(xknx.task_registry.tasks) == 0
        assert task._task is None
        await asyncio.sleep(0)  # iterate loop to cancel task
        assert self.test == 0
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 0

    async def test_background(self, time_travel):
        """Test running background task."""
        TIME = 10

        async def callback() -> None:
            """Do nothing."""
            await asyncio.sleep(TIME)

        xknx = XKNX()
        xknx.task_registry.background(callback())
        assert len(xknx.task_registry._background_task) == 1
        task = next(iter(xknx.task_registry._background_task))
        refs = sys.getrefcount(task)
        assert refs == 4
        assert not task.done()

        # after task is finished it should remove itself from the background registry
        await time_travel(TIME)
        assert len(xknx.task_registry._background_task) == 0
        assert task.done()
        refs = sys.getrefcount(task)
        assert refs == 2
