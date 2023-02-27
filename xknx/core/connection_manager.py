"""Manages connection callbacks."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from datetime import datetime
from typing import Callable

from xknx.core.connection_state import XknxConnectionState, XknxConnectionType

AsyncConnectionStateCallback = Callable[[XknxConnectionState], Awaitable[None]]


class ConnectionManager:
    """Manages connection state changes XKNX."""

    def __init__(self) -> None:
        """Initialize ConnectionState class."""
        self._main_loop: asyncio.AbstractEventLoop | None = None

        self.connected = asyncio.Event()
        self._state = XknxConnectionState.DISCONNECTED
        self._connection_state_changed_cbs: list[AsyncConnectionStateCallback] = []

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
        self, connection_state_changed_cb: AsyncConnectionStateCallback
    ) -> None:
        """Register callback for connection state being updated."""
        self._connection_state_changed_cbs.append(connection_state_changed_cb)

    def unregister_connection_state_changed_cb(
        self, connection_state_changed_cb: AsyncConnectionStateCallback
    ) -> None:
        """Unregister callback for connection state being updated."""
        if connection_state_changed_cb in self._connection_state_changed_cbs:
            self._connection_state_changed_cbs.remove(connection_state_changed_cb)

    async def connection_state_changed(
        self,
        state: XknxConnectionState,
        connection_type: XknxConnectionType = XknxConnectionType.NOT_CONNECTED,
    ) -> None:
        """Run registered callbacks in main loop. Set internal state flag."""
        if self._main_loop:
            asyncio.run_coroutine_threadsafe(
                self._connection_state_changed(state, connection_type), self._main_loop
            )
        else:
            await self._connection_state_changed(state, connection_type)

    async def _connection_state_changed(
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

        if tasks := [
            connection_state_change_cb(state)
            for connection_state_change_cb in self._connection_state_changed_cbs
        ]:
            await asyncio.gather(*tasks)

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
