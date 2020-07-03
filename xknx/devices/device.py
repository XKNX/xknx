"""
Device is the base class for all implemented devices (e.g. Lights/Switches/Sensors).

It provides basis functionality for reading the state from the KNX bus.
"""
import anyio

from xknx.exceptions import XKNXException
from xknx.telegram import Telegram, TelegramType

try:
    from contextlib import asynccontextmanager
except ImportError:
    from async_generator import asynccontextmanager

class Device:
    """Base class for devices."""

    def __init__(self, xknx, name, device_updated_cb=None):
        """Initialize Device class."""
        self.xknx = xknx
        self.name = name
        self.device_updated_cbs = []
        self.__evt = None
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

    def __repr__(self):
        return "<%s:%s>" % (self.__class__.__name__, self.name)

    @asynccontextmanager
    async def run(self):
        """Async context manager for using a device.

        The context adds the device to XKNX and returns an iterator which
        yields the device after an update.
        """
        if self.__evt is not None:
            raise RuntimeError("You cannot call 'Device.run' twice.")
        self.__evt = anyio.create_event()
        self.add_to_xknx()
        try:
            await self.sync(wait_for_result=False)
            yield self
        finally:
            self.remove_from_xknx()
            evt, self.__evt = self.__evt, None
            await evt.set()

    def __aiter__(self):
        """Async iterator setup (no-op)."""
        return self

    async def __anext__(self):
        """Async iterator for changes.

        This will coalesce multiple calls, which due to the async nature of
        xknx is inevitable anyway."""
        await self.__evt.wait()
        if self.__evt is None:
            raise StopAsyncIteration
        return self

    def register_device_updated_cb(self, device_updated_cb):
        """Register device updated callback."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(self, device_updated_cb):
        """Unregister device updated callback."""
        self.device_updated_cbs.remove(device_updated_cb)

    async def after_update(self):
        """Execute callbacks after internal state has changed."""
        if self.__evt is not None:
            evt, self.__evt = self.__evt, anyio.create_event()
            await evt.set()

        for device_updated_cb in self.device_updated_cbs:
            # pylint: disable=not-callable
            await device_updated_cb(self)

    async def sync(self, wait_for_result=True):
        """Read state of device from KNX bus."""
        try:
            await self._sync_impl(wait_for_result)
        except XKNXException as ex:
            self.xknx.logger.error("Error while syncing device: %s", ex)

    async def _sync_impl(self, wait_for_result=True):
        self.xknx.logger.debug("Sync %s", self.name)
        for group_address in self.state_addresses():
            from xknx.core import ValueReader  # pylint: disable=import-outside-toplevel
            value_reader = ValueReader(self.xknx, group_address)
            if wait_for_result:
                telegram = await value_reader.read()
                if telegram is not None:
                    await self.process(telegram)
                else:
                    self.xknx.logger.warning("Could not sync group address '%s' from %s", group_address, self)
            else:
                await value_reader.send_group_read()

    # TODO: remove need for send function in device - only use set and RemoteValue.send
    async def send(self, group_address, payload=None, response=False):
        """Send payload as telegram to KNX bus."""
        telegram = Telegram(group_address = group_address,
                payload = payload,
                telegramtype = TelegramType.GROUP_RESPONSE \
                    if response else TelegramType.GROUP_WRITE)
        await self.xknx.telegrams_out.put(telegram)

    def all_addresses(self):
        """Return all group addresses which this device uses"""
        return []

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        # pylint: disable=no-self-use
        return []

    async def process(self, telegram):
        """Process incoming telegram."""
        if telegram.telegramtype == TelegramType.GROUP_WRITE:
            await self.process_group_write(telegram)
        elif telegram.telegramtype == TelegramType.GROUP_RESPONSE:
            await self.process_group_response(telegram)
        elif telegram.telegramtype == TelegramType.GROUP_READ:
            await self.process_group_read(telegram)

    async def process_group_read(self, telegram):
        """Process incoming GroupValueRead telegrams."""
        # The dafault is, that devices dont answer to group reads

    async def process_group_response(self, telegram):
        """Process incoming GroupValueResponse telegrams."""
        # Per default mapped to group write.
        await self.process_group_write(telegram)

    async def process_group_write(self, telegram):
        """Process incoming GroupValueWrite telegrams."""
        # The dafault is, that devices dont process group writes

    def get_name(self):
        """Return name of device."""
        return self.name

    async def do(self, action):
        """Execute 'do' commands."""
        # pylint: disable=invalid-name
        self.xknx.logger.info("Do not implemented action '%s' for %s", action, self.__class__.__name__)

    def add_to_xknx(self):
        """Add myself to xknx's device list."""
        self.xknx.devices.add(self)

    def remove_from_xknx(self):
        """Remove myself from xknx's device list."""
        self.xknx.devices.remove(self)
