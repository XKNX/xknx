"""Unit test for connection manager."""
from datetime import datetime
import threading
from unittest.mock import AsyncMock, patch

from xknx import XKNX
from xknx.core import XknxConnectionState, XknxConnectionType
from xknx.io import ConnectionConfig
from xknx.util import asyncio_timeout


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
            XknxConnectionState.CONNECTED, XknxConnectionType.ROUTING_SECURE
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

    async def test_threaded_connection(self):
        """Test starting threaded connection."""
        # pylint: disable=attribute-defined-outside-init
        self.main_thread = threading.get_ident()
        xknx = XKNX(connection_config=ConnectionConfig(threaded=True))

        async def assert_main_thread(*args, **kwargs):
            """Test callback is done by main thread."""
            assert self.main_thread == threading.get_ident()

        xknx.connection_manager.register_connection_state_changed_cb(assert_main_thread)

        async def set_connected():
            """Set connected state."""
            await xknx.connection_manager.connection_state_changed(
                XknxConnectionState.CONNECTED
            )
            assert self.main_thread != threading.get_ident()

        with patch("xknx.io.KNXIPInterface._start", side_effect=set_connected):
            await xknx.start()
            # wait for side_effect to finish
            async with asyncio_timeout(1):
                await xknx.connection_manager.connected.wait()
            await xknx.stop()

    async def test_connection_information(self):
        """Test connection information."""
        xknx = XKNX()

        assert xknx.connection_manager.connected_since is None
        assert (
            xknx.connection_manager.connection_type is XknxConnectionType.NOT_CONNECTED
        )
        xknx.connection_manager.cemi_count_incoming = 5
        xknx.connection_manager.cemi_count_incoming_error = 5
        xknx.connection_manager.cemi_count_outgoing = 5
        xknx.connection_manager.cemi_count_outgoing_error = 5

        # reset counters on new connection
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED, XknxConnectionType.TUNNEL_TCP
        )
        assert xknx.connection_manager.cemi_count_incoming == 0
        assert xknx.connection_manager.cemi_count_incoming_error == 0
        assert xknx.connection_manager.cemi_count_outgoing == 0
        assert xknx.connection_manager.cemi_count_outgoing_error == 0
        assert isinstance(xknx.connection_manager.connected_since, datetime)
        assert xknx.connection_manager.connection_type is XknxConnectionType.TUNNEL_TCP

        xknx.connection_manager.cemi_count_incoming = 5
        xknx.connection_manager.cemi_count_incoming_error = 5
        xknx.connection_manager.cemi_count_outgoing = 5
        xknx.connection_manager.cemi_count_outgoing_error = 5
        # keep values until new connection; set connection timestamp to None
        await xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        assert xknx.connection_manager.cemi_count_incoming == 5
        assert xknx.connection_manager.cemi_count_incoming_error == 5
        assert xknx.connection_manager.cemi_count_outgoing == 5
        assert xknx.connection_manager.cemi_count_outgoing_error == 5
        assert xknx.connection_manager.connected_since is None
        assert (
            xknx.connection_manager.connection_type is XknxConnectionType.NOT_CONNECTED
        )
