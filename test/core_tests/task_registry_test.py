"""Unit test for task registry."""
import asyncio

import pytest
from xknx import XKNX
from xknx.core import XknxConnectionState


@pytest.mark.asyncio
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
            task=callback(),
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        await xknx.task_registry.block_till_done()
        assert len(xknx.task_registry.tasks) == 0

    async def test_unregister(self):
        """Test unregister after register."""

        xknx = XKNX()

        async def callback() -> None:
            """Do nothing."""

        task = xknx.task_registry.register(
            name="test",
            task=callback(),
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        xknx.task_registry.unregister(task.name)
        assert len(xknx.task_registry.tasks) == 0

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
            task=callback(),
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        xknx.task_registry.stop()
        assert len(xknx.task_registry.tasks) == 0

    #
    # TEST CONNECTION HANDLING
    #
    async def test_reconnect_handling(self):
        """Test reconnect handling."""

        xknx = XKNX()
        xknx.task_registry.start()
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 1
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )

        async def callback() -> None:
            """Reset tasks."""
            await asyncio.sleep(100)

        task = xknx.task_registry.register(
            name="test", task=callback(), restart_after_reconnect=True
        )
        assert len(xknx.task_registry.tasks) == 1
        task.start()
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        assert task._task is None
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        assert task._task is not None
        assert len(xknx.task_registry.tasks) == 1

        xknx.task_registry.stop()
        assert len(xknx.task_registry.tasks) == 0
        assert task._task is None
        assert len(xknx.connection_manager._connection_state_changed_cbs) == 0
