import asyncio
from time import sleep
from functools import partial


class StateUpdater():
    """Class for reading the value of a RemoteValue from KNX bus."""

    def __init__(self,
                 xknx,
                 expiration_min=60,
                 callback=None):
        """Initialize StateUpdater class."""
        self.xknx = xknx
        self.timeout = expiration_min
        self._run_task = None
        self._callback = callback
        self.index = 1

    def start(self):
        """Start StateUpdater."""
        print("starting...", self.index)
        self._run_task = self.xknx.loop.create_task(
            self._run(self.index))
        # self._run_task.add_done_callback()
        # asyncio.Task.add_done_callback
        self.index += 1

    def stop(self):
        self._run_task.cancel()
        self._run_task.cancel()

    async def _run(self, index):
        """Worker task. Endless loop for updating states."""
        iteration = 0
        while True:
            iteration += 1
            try:
                print("async sleeping...", index, iteration)
                await asyncio.sleep(self.timeout)
                # TODO: is RV.read_state canceled from process() on reset without shield?
            except asyncio.CancelledError:
                print("_run cancelled", index, iteration)
                return
            print("callback...", index)
            self.xknx.loop.create_task(self._callback(index, iteration))
            # await asyncio.shield(self._run_cb(index, iteration))

    async def _run_cb(self, index, iteration):
        await self._callback(index, iteration)
        print("callback finished", index)

    async def reset(self):
        """Restart worker task."""
        # try:
        #     self._run_task.cancel()
        #     await self._run_task
        # except asyncio.CancelledError:
        #     print("cancelled error - restarting")
        #     self.start()
        self.stop()
        self.start()


class Xknx():
    def __init__(self, loop):
        self.loop = loop


class Test():
    def __init__(self, xknx):
        self.xknx = xknx
        self._tick = 0
        self.state_updater = StateUpdater(
            self.xknx,
            callback=self.cb,
            expiration_min=1)
        self.state_updater.start()
        self.xknx.loop.create_task(self.can())

    async def cb(self, index, iteration):
        # sleep(1)
        print("cb start sleep", index)
        await asyncio.sleep(0.5)
        print("cb woke up sleep", index)
        if index is 3 and iteration is not 2:
            return

        await self.state_updater.reset()
        print("reseted state_updater from callback", index)

    async def can(self):
        await asyncio.sleep(1.2)
        print("shooting task")
        await self.state_updater.reset()


async def main(loop):
    xknx = Xknx(loop)
    test = Test(xknx)
    for _ in range(10):
        await asyncio.sleep(1)
        # print("async tick")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
