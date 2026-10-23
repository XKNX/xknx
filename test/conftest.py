"""Conftest for XKNX."""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX


class EventLoopClockAdvancer:
    """Allow advancing of loop time."""

    # thanks to @dermotduffy for his asyncio.sleep mock
    # https://github.com/dermotduffy/hyperion-py/blob/main/tests/client_test.py#L273

    __slots__ = ("_loop_start", "_perf_start", "loop", "offset")

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """Initialize."""
        self.offset = 0.0
        self.loop = loop
        # The loop clock (time.monotonic) ticks in steps of 15.6 ms on Windows, and the
        # loop runs every timer due within that resolution. Follow it with the
        # high-resolution performance counter instead, so an advance by a few
        # milliseconds is exact there too.
        self._loop_start = loop.time()
        self._perf_start = time.perf_counter()
        self.loop._clock_resolution = time.get_clock_info("perf_counter").resolution  # type: ignore[attr-defined]

        # incorporate offset timing into the event loop
        self.loop.time = self.time  # type: ignore[method-assign]

    def time(self) -> float:
        """Return loop time adjusted by offset."""
        return self._loop_start + (time.perf_counter() - self._perf_start) + self.offset

    async def _exhaust_callbacks(self) -> None:
        """Run the loop until all ready callbacks are executed."""
        while self.loop._ready:  # type: ignore[attr-defined] # noqa: ASYNC110
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
async def time_travel() -> EventLoopClockAdvancer:
    """Advance loop time and run callbacks."""
    event_loop = asyncio.get_running_loop()
    return EventLoopClockAdvancer(event_loop)


@pytest.fixture
def xknx_no_interface() -> XKNX:
    """Return XKNX instance without KNX/IP interface."""

    def knx_ip_interface_mock() -> Mock:
        """Create a xknx knx ip interface mock."""
        mock = Mock()
        mock.start = AsyncMock()
        mock.stop = AsyncMock()
        mock.send_cemi = AsyncMock()
        return mock

    with patch("xknx.xknx.knx_interface_factory", return_value=knx_ip_interface_mock()):
        return XKNX()
