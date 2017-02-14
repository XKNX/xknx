import asyncio

class StateUpdater():

    def __init__(self,
                 xknx,
                 timeout=600,
                 start_timeout=15,
                 sleep_during_devices=0.2):
        self.xknx = xknx
        self.timeout = timeout
        self.start_timeout = start_timeout
        self.sleep_during_devices = sleep_during_devices

    @asyncio.coroutine
    def start(self):
        self.xknx.loop.create_task(
            self.run())

    @asyncio.coroutine
    def run(self):
        yield from asyncio.sleep(self.start_timeout)
        print("Starting Update Thread")
        while True:
            yield from self.sync_states()
            yield from asyncio.sleep(self.timeout)

    @asyncio.coroutine
    def sync_states(self):
        for device in self.xknx.devices:
            device.sync_state()
            yield from asyncio.sleep(self.sleep_during_devices)
