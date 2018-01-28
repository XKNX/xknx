"""Module for reading the values of all devices from device vector from KNX bus in periodic cycles."""
import asyncio


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

    async def start(self):
        """Start StateUpdater."""
        self.run_task = self.xknx.loop.create_task(
            self.run())

    async def run(self):
        """Worker thread. Endless loop for updating states."""
        await asyncio.sleep(self.start_timeout)
        self.xknx.logger.debug("Starting StateUpdater")
        while True:
            await self.xknx.devices.sync()
            await asyncio.sleep(self.timeout)
            if not self.run_forever:
                break
