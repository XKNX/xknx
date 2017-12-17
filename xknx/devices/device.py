"""
Device is the base class for all implemented devices (e.g. Lights/Switches/Sensors).

It provides basis functionality for reading the state from the KNX bus.
"""
import asyncio

from xknx.knx import Telegram


class Device:
    """Base class for devices."""

    def __init__(self, xknx, name, device_updated_cb=None):
        """Initialize Device class."""
        self.xknx = xknx
        self.name = name
        self.device_updated_cbs = []
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

    def register_device_updated_cb(self, device_updated_cb):
        """Register device updated callback."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        """Unregister device updated callback."""
        self.device_updated_cbs.remove(device_updated_cb)

    @asyncio.coroutine
    def after_update(self):
        """Execute callbacks after internal state has been changed."""
        for device_updated_cb in self.device_updated_cbs:
            # pylint: disable=not-callable
            yield from device_updated_cb(self)

    @asyncio.coroutine
    def sync(self, wait_for_result=True):
        """Read state of device from KNX bus."""
        self.xknx.logger.debug("Sync %s", self.name)
        for group_address in self.state_addresses():
            from xknx.core import ValueReader
            value_reader = ValueReader(self.xknx, group_address)
            if wait_for_result:
                telegram = yield from value_reader.read()
                if telegram is not None:
                    yield from self.process(value_reader.received_telegram)
                else:
                    self.xknx.logger.warning("Could not read value of %s %s", self, group_address)
            else:
                yield from value_reader.send_group_read()

    # XXX no longer needed!
    @asyncio.coroutine
    def send(self, group_address, payload=None):
        """Send payload as telegram to KNX bus."""
        telegram = Telegram()
        telegram.group_address = group_address
        telegram.payload = payload
        yield from self.xknx.telegrams.put(telegram)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        # pylint: disable=no-self-use
        return []

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        pass

    def get_name(self):
        """Return name of device."""
        return self.name

    @asyncio.coroutine
    def do(self, action):
        """Execute 'do' commands."""
        # pylint: disable=invalid-name
        pass
