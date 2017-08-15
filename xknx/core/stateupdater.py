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

    @asyncio.coroutine
    def start(self):
        """Start StateUpdater."""
        self.xknx.loop.create_task(
            self.run())

    @asyncio.coroutine
    def run(self):
        """Worker thread. Endless loop for updating states."""
        yield from asyncio.sleep(self.start_timeout)
        self.xknx.logger.debug("Starting StateUpdater")
        while True:
            yield from self.xknx.devices.sync()
            yield from asyncio.sleep(self.timeout)
