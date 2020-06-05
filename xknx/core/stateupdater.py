"""Module for reading the values of all devices from device vector from KNX bus in periodic cycles."""
import anyio

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
        self.run_task = None

    async def start(self):
        """Start StateUpdater."""
        self.run_task = await self.xknx.spawn(self._run)

    async def stop(self):
        """Stop StateUpdater."""
        if self.run_task:
            self.xknx.logger.debug("Stopping StateUpdater")
            await self.run_task.cancel()
            self.run_task = None

    async def _run(self):
        """Worker thread. Endless loop for updating states."""
        await anyio.sleep(self.start_timeout)
        self.xknx.logger.debug("Starting StateUpdater")
        while True:
            await self.xknx.devices.sync()
            await anyio.sleep(self.timeout)
