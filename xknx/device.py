import asyncio
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
                yield from value_reader.async_start()
                if value_reader.success:
                    self.process(value_reader.received_telegram)
                else:
                    print("Could not sync state for {0} {1}".format(self, group_address))
            else:
                yield from value_reader.send_group_read()



    # returning group_addresses which should be requested to sync state
    def state_addresses(self):
        # pylint: disable=no-self-use
        return []

    def process(self, telegram):
        pass

    def get_name(self):
        return self.name

    # pylint: disable=invalid-name
    def do(self, action):
        pass
