"""Unit test for connection manager."""
import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from xknx import XKNX
from xknx.core import XknxConnectionState
from xknx.dpt import DPTBinary
from xknx.exceptions import CommunicationError, CouldNotParseTelegram
from xknx.telegram import AddressFilter, Telegram, TelegramDirection
from xknx.telegram.address import GroupAddress, InternalGroupAddress
from xknx.telegram.apci import GroupValueWrite


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
        xknx.connection_manager.register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        async_connection_state_changed_cb.assert_called_once_with(
            XknxConnectionState.CONNECTED
        )

    async def test_unregister(self):
        """Test unregister after register."""

        xknx = XKNX()
        async_connection_state_changed_cb = AsyncMock()
        xknx.connection_manager.register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        xknx.connection_manager.unregister_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        async_connection_state_changed_cb.assert_not_called()

    #
    # TEST PROCESS
    #
    async def test_state_return(self):
        """Test should return if current state equals parameter."""

        xknx = XKNX()
        async_connection_state_changed_cb = AsyncMock()
        xknx.connection_manager.register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )
        assert xknx.connection_manager.state == XknxConnectionState.DISCONNECTED
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        async_connection_state_changed_cb.assert_not_called()

    #
    # TEST CONNECTED
    #
    async def test_connected_event(self):
        """Test connected event callback."""

        xknx = XKNX()
        async_connection_state_changed_cb = AsyncMock()
        xknx.connection_manager.register_connection_state_changed_cb(
            async_connection_state_changed_cb
        )

        assert not xknx.connection_manager.connected.is_set()

        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED
        )
        async_connection_state_changed_cb.assert_called_once_with(
            XknxConnectionState.CONNECTED
        )

        assert xknx.connection_manager.connected.is_set()
