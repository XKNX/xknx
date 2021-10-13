"""Manages connection callbacks."""
from __future__ import annotations

import asyncio
from typing import Awaitable, Callable

from xknx.core.connection_state import XknxConnectionState

AsyncConnectionStateCallback = Callable[[XknxConnectionState], Awaitable[None]]


class ConnectionManager:
    """Manages connection state changes XKNX."""

    def __init__(self) -> None:
        """Initialize ConnectionState class."""
        self.connected = asyncio.Event()
        self._state = XknxConnectionState.DISCONNECTED
        self._connection_state_changed_cbs: list[AsyncConnectionStateCallback] = []

    def register_connection_state_changed_cb(
        self, connection_state_changed_cb: AsyncConnectionStateCallback
    ) -> None:
        """Register callback for connection state beeing updated."""
        self._connection_state_changed_cbs.append(connection_state_changed_cb)

    def unregister_connection_state_changed_cb(
        self, connection_state_changed_cb: AsyncConnectionStateCallback
    ) -> None:
        """Unregister callback for connection state beeing updated."""
        self._connection_state_changed_cbs.remove(connection_state_changed_cb)

    async def connection_state_changed(self, state: XknxConnectionState) -> None:
        """Run registered callbacks. Set internal state flag."""
        if self._state == state:
            return

        self._state = state
        if state == XknxConnectionState.CONNECTED:
            self.connected.set()
        else:
            self.connected.clear()
        for connection_state_changed_cb in self._connection_state_changed_cbs:
            await connection_state_changed_cb(state)

    @property
    def state(self) -> XknxConnectionState:
        """Get current state."""
        return self._state
