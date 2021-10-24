"""Unit test for connection manager."""
from unittest.mock import AsyncMock

import pytest
from xknx import XKNX
from xknx.core import ConnectionManager, XknxConnectionState


@pytest.mark.asyncio
class TestConnectionManager:
    """Test class for connection manager."""

    #
    # TEST REGISTER/UNREGISTER
    #
    async def test_register(self):
        """Test connection_state_changed after register."""

        xknx = XKNX()
        async_connection_state_changed_cb = AsyncMock()
        xknx.get_connection_manager().register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        await xknx.get_connection_manager().connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        async_connection_state_changed_cb.assert_called_once_with(
            XknxConnectionState.CONNECTED
        )

    async def test_unregister(self):
        """Test unregister after register."""

        connection_manager = ConnectionManager()
        async_connection_state_changed_cb = AsyncMock()
        connection_manager.register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        connection_manager.unregister_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        await connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        async_connection_state_changed_cb.assert_not_called()

    #
    # TEST PROCESS
    #
    async def test_state_return(self):
        """Test should return if current state equals parameter."""

        xknx = XKNX()
        async_connection_state_changed_cb = AsyncMock()
        xknx.get_connection_manager().register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        assert xknx.get_connection_manager().state == XknxConnectionState.DISCONNECTED
        await xknx.get_connection_manager().connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        async_connection_state_changed_cb.assert_not_called()

    #
    # TEST CONNECTED
    #
    async def test_connected_event(self):
        """Test connected event callback."""

        connection_manager = ConnectionManager()
        async_connection_state_changed_cb = AsyncMock()
        connection_manager.register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )

        assert not connection_manager.connected.is_set()

        await connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        async_connection_state_changed_cb.assert_called_once_with(
            XknxConnectionState.CONNECTED
        )

        assert connection_manager.connected.is_set()
