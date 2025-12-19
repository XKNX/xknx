"""Conftest for XKNX."""

import asyncio
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from xknx import XKNX


class EventLoopClockAdvancer:
    """Allow advancing of loop time."""

    # thanks to @dermotduffy for his asyncio.sleep mock
    # https://github.com/dermotduffy/hyperion-py/blob/main/tests/client_test.py#L273

    __slots__ = ("_base_time", "loop", "offset")

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        """Initialize."""
        self.offset = 0.0
        self._base_time = loop.time
        self.loop = loop

        # incorporate offset timing into the event loop
        self.loop.time = self.time  # type: ignore[method-assign]

    def time(self) -> float:
        """Return loop time adjusted by offset."""
        return self._base_time() + self.offset

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


# py3.10 doesn't properly support patch() with wraps and autospec https://github.com/python/cpython/pull/117124
skip_3_10 = pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="requires Python 3.11 or higher",
)
