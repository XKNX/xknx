"""Module for reading the values of all devices from device vector from KNX bus in periodic cycles."""
import asyncio

from contextlib import asynccontextmanager

class StateUpdater():
    """Class for reading the values of all devices from KNX bus."""

    def __init__(self,
                 xknx,
                 timeout=3600,
                 start_timeout=10):
        """Initialize StateUpdater class."""
        self.xknx = xknx
        self.timeout = timeout
        self.start_timeout = start_timeout
        self.run_forever = True
        self.run_task = None

    @asynccontextmanager
    async def run(self):
        try:
            await self.start()
            yield self
        finally:
            await self.stop()

    async def start(self):
        """Start StateUpdater."""
        self.run_task = asyncio.create_task(
            self._run())

    async def stop(self):
        """Stop StateUpdater."""
        if self.run_task:
            self.xknx.logger.debug("Stopping StateUpdater")
            self.run_task.cancel()
            try:
                await self.run_task
            except asyncio.CancelledError:
                self.run_task = None

    async def _run(self):
        """Worker thread. Endless loop for updating states."""
        await asyncio.sleep(self.start_timeout)
        self.xknx.logger.debug("Starting StateUpdater")
        while True:
            await self.xknx.devices.sync()
            await asyncio.sleep(self.timeout)
            if not self.run_forever:
                break
