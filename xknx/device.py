import asyncio
from xknx.knx import Telegram
from .value_reader import ValueReader

class Device:
    def __init__(self, xknx, name, device_updated_cb=None):
        self.xknx = xknx
        self.name = name
        self.device_updated_cbs = []
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

    def register_device_updated_cb(self, device_updated_cb):
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        self.device_updated_cbs.remove(device_updated_cb)

    def after_update(self):
        for device_updated_cb in self.device_updated_cbs:
            # pylint: disable=not-callable
            device_updated_cb(self)

    @asyncio.coroutine
    def sync(self, wait_for_result=True):
        print("Sync {0}".format(self.name))
        for group_address in self.state_addresses():
            value_reader = ValueReader(self.xknx, group_address)
            if wait_for_result:
                telegram = yield from value_reader.read()
                if telegram is not None:
                    self.process(value_reader.received_telegram)
                else:
                    print("Could not read value of {0} {1}".format(self, group_address))
            else:
                yield from value_reader.send_group_read()

    def send(self, group_address, payload=None):
        """Sends payload as telegram to KNX bus."""
        telegram = Telegram()
        telegram.group_address = group_address
        telegram.payload = payload
        self.xknx.telegrams.put_nowait(telegram)

    def state_addresses(self):
        """Returns group addresses which should be requested to sync state."""
        # pylint: disable=no-self-use
        return []

    def process(self, telegram):
        pass

    def get_name(self):
        return self.name

    # pylint: disable=invalid-name
    def do(self, action):
        pass
