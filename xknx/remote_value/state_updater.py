"""Module for keeping the value of a RemoteValue from KNX bus up to date."""
import asyncio


class StateUpdater():
    """Class for reading the value of a RemoteValue from KNX bus."""

    def __init__(self,
                 xknx,
                 expiration_min=60,
                 callback=None):
        """Initialize StateUpdater class."""
        self.xknx = xknx
        self.timeout = expiration_min * 60
        # TODO: naming? async_callback?
        # maybe save reference to RemoteValue instead of callback
        self._callback = callback
        # TODO: should we start from __init__ or manualy?
        self._waiting_task = None
        self._callback_task = self.xknx.loop.create_task(
            self._initial_start())

    def start(self):
        """Start StateUpdater - wait for value to expire."""
        self._waiting_task = self.xknx.loop.create_task(
            self._wait_for_expiration())

    async def stop(self):
        """Stop StateUpdater."""
        self._waiting_task.cancel()
        self._callback_task.cancel()
        await self._callback_task()

    def reset(self):
        """Restart the timer."""
        self._waiting_task.cancel()
        self.start()

    async def _initial_start(self):
        """Start StateUpdater - read state on call."""
        await self.xknx.started.wait()
        # TODO: random(1-15) start timeout so not all devices are queried at once?
        self.start()
        self._run_callback()

    async def _wait_for_expiration(self):
        """Waits for the timeout to expire. Endless loop for updating states."""
        # on successfull reading the 2nd iteration of the while loop gets canceled when the callback calls reset()
        # when no telegram was received it will try again endlessly
        while True:
            try:
                await asyncio.sleep(self.timeout)
            except asyncio.CancelledError:
                return
            self._run_callback()

    def _run_callback(self):
        # TODO: log name of remote value for debugging?
        self.xknx.logger.debug("StateUpdater scheduling reading of group address")
        self._callback_task = self.xknx.loop.create_task(self._callback())
