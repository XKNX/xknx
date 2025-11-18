"""Unit test for connection manager."""

import asyncio
from datetime import datetime
import threading
from typing import Any
from unittest.mock import Mock, patch

from xknx import XKNX
from xknx.core import XknxConnectionState, XknxConnectionType
from xknx.io import ConnectionConfig
from xknx.util import asyncio_timeout


class TestConnectionManager:
    """Test class for connection manager."""

    #
    # TEST REGISTER/UNREGISTER
    #
    async def test_register(self) -> None:
        """Test connection_state_changed after register."""

        xknx = XKNX()
        connection_state_changed_cb = Mock()
        xknx.connection_manager.register_connection_state_changed_cb(
            connection_state_changed_cb
        )
        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.CONNECTED, XknxConnectionType.ROUTING_SECURE
        )
        connection_state_changed_cb.assert_called_once_with(
            XknxConnectionState.CONNECTED
        )

    async def test_unregister(self) -> None:
        """Test unregister after register."""

        xknx = XKNX()
        connection_state_changed_cb = Mock()
        xknx.connection_manager.register_connection_state_changed_cb(
            connection_state_changed_cb
        )
        xknx.connection_manager.unregister_connection_state_changed_cb(
            connection_state_changed_cb
        )
        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        connection_state_changed_cb.assert_not_called()

    #
    # TEST PROCESS
    #
    async def test_state_return(self) -> None:
        """Test should return if current state equals parameter."""

        xknx = XKNX()
        connection_state_changed_cb = Mock()
        xknx.connection_manager.register_connection_state_changed_cb(
            connection_state_changed_cb
        )
        assert xknx.connection_manager.state == XknxConnectionState.DISCONNECTED
        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )
        connection_state_changed_cb.assert_not_called()

    #
    # TEST CONNECTED
    #
    async def test_connected_event(self) -> None:
        """Test connected event callback."""

        xknx = XKNX()
        connection_state_changed_cb = Mock()
        xknx.connection_manager.register_connection_state_changed_cb(
            connection_state_changed_cb
        )

        assert not xknx.connection_manager.connected.is_set()

        xknx.connection_manager.connection_state_changed(XknxConnectionState.CONNECTED)
        connection_state_changed_cb.assert_called_once_with(
            XknxConnectionState.CONNECTED
        )

        assert xknx.connection_manager.connected.is_set()

    async def test_threaded_connection(self) -> None:
        """Test starting threaded connection."""
        # pylint: disable=attribute-defined-outside-init
        self.main_thread = threading.get_ident()
        xknx = XKNX(connection_config=ConnectionConfig(threaded=True))

        def assert_main_thread(*args: Any, **kwargs: dict[str, Any]) -> None:
            """Test callback is done by main thread."""
            assert self.main_thread == threading.get_ident()

        xknx.connection_manager.register_connection_state_changed_cb(assert_main_thread)

        async def set_connected() -> None:
            """Set connected state."""
            xknx.connection_manager.connection_state_changed(
                XknxConnectionState.CONNECTED
            )
            assert self.main_thread != threading.get_ident()

        with patch("xknx.io.KNXIPInterface._start", side_effect=set_connected):
            await xknx.start()
            # wait for side_effect to finish
            async with asyncio_timeout(1):
                await xknx.connection_manager.connected.wait()
                await asyncio.sleep(0)
            await xknx.stop()

    async def test_connection_information(self) -> None:
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
        xknx.connection_manager.connection_state_changed(
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
        xknx.connection_manager.connection_state_changed(
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

    async def test_closed_event_loop(self) -> None:
        """Test connection_state_changed with closed event loop doesn't crash."""
        xknx = XKNX()

        # Register the loop
        await xknx.connection_manager.register_loop()

        # Close the event loop by mocking it
        closed_loop = Mock()
        closed_loop.call_soon_threadsafe.side_effect = RuntimeError(
            "Event loop is closed"
        )
        xknx.connection_manager._main_loop = closed_loop

        # This should not raise an exception
        xknx.connection_manager.connection_state_changed(
            XknxConnectionState.DISCONNECTED
        )

        # Verify call_soon_threadsafe was called
        closed_loop.call_soon_threadsafe.assert_called_once()
