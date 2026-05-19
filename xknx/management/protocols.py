"""Protocols for KNX management operations."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import AbstractAsyncContextManager
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from xknx.telegram.address import IndividualAddress
from xknx.telegram.apci import APCI

if TYPE_CHECKING:
    from xknx.telegram import Telegram


@runtime_checkable
class P2PConnection(Protocol):
    """Protocol for an established point-to-point connection (internal use)."""

    address: IndividualAddress

    async def request(self, payload: APCI, expected: type[APCI] | None) -> Telegram:
        """Send payload and wait for an expected response."""
        ...

    async def send_data_no_ack(self, payload: APCI) -> None:
        """Send payload without waiting for an ACK."""
        ...


@runtime_checkable
class ConnectionManager(Protocol):
    """Protocol for procedures that need to create P2P connections."""

    def connection(
        self, address: IndividualAddress
    ) -> AbstractAsyncContextManager[P2PConnection]:
        """Return an async context manager that opens a P2P connection to address."""
        ...


@runtime_checkable
class BroadcastContext(Protocol):
    """Protocol for a broadcast context that yields incoming broadcast telegrams."""

    def receive(self, timeout: float | None = 3) -> AsyncGenerator[Telegram, None]:
        """Yield incoming broadcast telegrams until timeout."""
        ...


@runtime_checkable
class Broadcaster(Protocol):
    """Protocol for procedures that only need broadcast send/receive capability."""

    async def send_broadcast(self, payload: APCI) -> None:
        """Send a broadcast telegram."""
        ...

    def broadcast(self) -> AbstractAsyncContextManager[BroadcastContext]:
        """Return an async context manager for receiving broadcast responses."""
        ...
