"""Conftest for XKNX."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX


class EventLoopClockAdvancer:
    """Allow advancing of loop time."""

    # thanks to @dermotduffy for his asyncio.sleep mock
    # https://github.com/dermotduffy/hyperion-py/blob/main/tests/client_test.py#L273

    __slots__ = ("offset", "loop", "_base_time")

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """Initialize."""
        self.offset = 0.0
        self._base_time = loop.time
        self.loop = loop

        # incorporate offset timing into the event loop
        self.loop.time = self.time  # type: ignore[assignment]

    def time(self) -> float:
        """Return loop time adjusted by offset."""
        return self._base_time() + self.offset

    async def _exhaust_callbacks(self) -> None:
        """Run the loop until all ready callbacks are executed."""
        while self.loop._ready:  # noqa: ASYNC110  # type: ignore[attr-defined]
            await asyncio.sleep(0)

    async def __call__(self, seconds: float) -> None:
        """Advance time by a given offset in seconds."""
        # Exhaust all callbacks.
        await self._exhaust_callbacks()

        if seconds > 0:
            # advance the clock by the given offset
            self.offset += seconds
            # Once the clock is adjusted, new tasks may have just been
            # scheduled for running in the next pass through the event loop
            await asyncio.sleep(0)
            await self._exhaust_callbacks()


@pytest.fixture
def time_travel(event_loop: asyncio.AbstractEventLoop) -> EventLoopClockAdvancer:
    """Advance loop time and run callbacks."""
    return EventLoopClockAdvancer(event_loop)


@pytest.fixture
def xknx_no_interface():
    """Return XKNX instance without KNX/IP interface."""

    def knx_ip_interface_mock():
        """Create a xknx knx ip interface mock."""
        mock = Mock()
        mock.start = AsyncMock()
        mock.stop = AsyncMock()
        mock.send_cemi = AsyncMock()
        return mock

    with patch("xknx.xknx.knx_interface_factory", return_value=knx_ip_interface_mock()):
        return XKNX()
