"""Manages connection callbacks."""

from __future__ import annotations

import asyncio
from datetime import datetime

from xknx.core.connection_state import XknxConnectionState, XknxConnectionType
from xknx.typing import ConnectionChangeCallbackType


class ConnectionManager:
    """Manages connection state changes XKNX."""

    def __init__(self) -> None:
        """Initialize ConnectionState class."""
        self._main_loop: asyncio.AbstractEventLoop | None = None

        self.connected = asyncio.Event()
        self._state = XknxConnectionState.DISCONNECTED
        self._connection_state_changed_cbs: list[ConnectionChangeCallbackType] = []

        self.cemi_count_incoming: int = 0
        self.cemi_count_incoming_error: int = 0
        self.cemi_count_outgoing: int = 0
        self.cemi_count_outgoing_error: int = 0
        self.connected_since: datetime | None = None
        self.connection_type: XknxConnectionType = XknxConnectionType.NOT_CONNECTED

    async def register_loop(self) -> None:
        """Register main loop to enable thread-safe `connection_state_changed` calls."""
        self._main_loop = asyncio.get_running_loop()

    def register_connection_state_changed_cb(
        self, connection_state_changed_cb: ConnectionChangeCallbackType
    ) -> None:
        """Register callback for connection state being updated."""
        self._connection_state_changed_cbs.append(connection_state_changed_cb)

    def unregister_connection_state_changed_cb(
        self, connection_state_changed_cb: ConnectionChangeCallbackType
    ) -> None:
        """Unregister callback for connection state being updated."""
        if connection_state_changed_cb in self._connection_state_changed_cbs:
            self._connection_state_changed_cbs.remove(connection_state_changed_cb)

    def connection_state_changed(
        self,
        state: XknxConnectionState,
        connection_type: XknxConnectionType = XknxConnectionType.NOT_CONNECTED,
    ) -> None:
        """Run registered callbacks in main loop. Set internal state flag."""
        if self._main_loop:
            self._main_loop.call_soon_threadsafe(
                self._connection_state_changed, state, connection_type
            )
        else:
            self._connection_state_changed(state, connection_type)

    def _connection_state_changed(
        self, state: XknxConnectionState, connection_type: XknxConnectionType
    ) -> None:
        """Run registered callbacks. Set internal state flag."""
        if self._state == state:
            return

        self._state = state
        self.connection_type = connection_type
        if state == XknxConnectionState.CONNECTED:
            self.connected.set()
            self._reset_counters()
        else:
            self.connected.clear()
            self.connected_since = None

        for connection_state_change_cb in self._connection_state_changed_cbs:
            connection_state_change_cb(state)

    @property
    def state(self) -> XknxConnectionState:
        """Get current state."""
        return self._state

    def _reset_counters(self) -> None:
        """Reset counters."""
        self.cemi_count_incoming = 0
        self.cemi_count_incoming_error = 0
        self.cemi_count_outgoing = 0
        self.cemi_count_outgoing_error = 0
        self.connected_since = datetime.now().astimezone()
