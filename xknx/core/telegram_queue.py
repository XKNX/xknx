"""
Module for queing telegrams.

When a device wants to sends a telegram to the KNX bus, it has to queue it to the TelegramQueue within XKNX.

The underlaying KNXIPInterface will poll the queue and send the packets to the correct KNX/IP abstraction (Tunneling or Routing).

You may register callbacks to be notified if a telegram was pushed to the queue.
"""
import anyio
from contextlib import contextmanager
from distkv.util import create_queue  # XXX vendorize it myself?

try:
    from contextlib import asynccontextmanager
except ImportError:
    from async_generator import asynccontextmanager


class _TelegramQueue():
    """Class for telegram queue."""

    class Callback:
        """Callback class for handling telegram received callbacks."""

        # pylint: disable=too-few-public-methods

        def __init__(self, callback, address_filters=None):
            """Initialize Callback class."""
            self.callback = callback
            self.address_filters = address_filters

        def is_within_filter(self, telegram):
            """Test if callback is filtering for group address."""
            if not self.address_filters:
                return True
            for address_filter in self.address_filters:
                if address_filter.match(telegram.group_address):
                    return True
            return False

        async def __call__(self, telegram):
            """Call the callback if not filtered off."""
            if not self.is_within_filter(telegram):
                return False
            return await self.callback(telegram)

    def __init__(self, xknx, rate_limit=0):
        """Initialize TelegramQueue class."""
        self.xknx = xknx
        self.q = create_queue(10)
        self.callbacks = set()
        self.queue_stopped = anyio.create_event()
        self.rate_limit = rate_limit

    def register_telegram_cb(self, telegram_cb, address_filters=None):
        """Register callback for a telegram beeing received from KNX bus."""
        callback = _TelegramQueue.Callback(telegram_cb, address_filters)
        self.callbacks.add(callback)
        return callback

    def unregister_telegram_cb(self, telegram_cb):
        """Unregister callback for a telegram beeing received from KNX bus."""
        self.callbacks.remove(telegram_cb)

    @contextmanager
    def receiver(self, *address_filters):
        """Context manager returning an iterator for queued telegrams."""
        q = anyio.create_queue(10)

        async def _receiver(telegram, _=None):
            await q.put(telegram)

        callb = _TelegramQueue.Callback(_receiver, address_filters)
        try:
            self.callbacks.add(callb)
            yield q
        finally:
            self.callbacks.remove(callb)

    @asynccontextmanager
    async def run_test(self):
        """Async context manager to manage the telegram queue.

        XKNX only uses this method for testing.
        """
        if self.xknx.task_group is not None:
            raise RuntimeError("This function is only used for testing.")
        async with anyio.create_task_group() as tg:
            self.xknx.task_group = tg
            try:
                await self.start()
                yield self
            finally:
                self.xknx.task_group = None
                await self.stop()

    async def start(self):
        """Start telegram queue."""
        await self.xknx.spawn(self._run)

    async def put(self, telegram):
        """Enqueue a telegram."""
        await self.q.put(telegram)

    def qsize(self):
        """Return the size of this queue."""
        return self.q.qsize()

    async def _run(self):
        """Endless loop for processing telegrams."""
        try:
            while True:
                telegram = await self.q.get()
                if telegram is None:
                    return
                await self.process_telegram(telegram)
                if self.rate_limit:
                    await anyio.sleep(1 / self.rate_limit)
        finally:
            await self.queue_stopped.set()

    async def stop(self):
        """Stop telegram queue."""
        self.xknx.logger.debug("Stopping TelegramQueue")
        # If a None object is pushed to the queue, the queue stops
        await self.q.put(None)
        await self.queue_stopped.wait()

    async def process_all_telegrams(self):
        """Process all queued telegrams.

        Only used for testing.
        """
        while not self.q.empty():
            telegram = await self.q.get()
            await self.process_telegram(telegram)

    async def process_telegram(self, telegram):
        """Process one queued telegram.

        Called from reader task.
        """
        processed = False
        for cb in list(self.callbacks):
            processed = await cb(telegram) or processed
        return processed


class TelegramQueueIn(_TelegramQueue):
    """A Telegram queue that processes incoming telegrams."""

    async def process_telegram(self, telegram):
        """Distribute to callbacks and devices."""
        processed = await super().process_telegram(telegram)

        # This code previously blocked distributing to devices when
        # a telegram was accepted by one of the receivers, but that
        # does not make much sense.
        if self.xknx.devices:
            for device in self.xknx.devices.devices_by_group_address(
                    telegram.group_address):
                await device.process(telegram)
                processed = True
        return processed


class TelegramQueueOut(_TelegramQueue):
    """A Telegram queue that sends off outgoing telegrams."""

    _out_cb = None

    async def start(self):
        """Start processing."""
        await super().start()

        async def _out_callback(telegram):
            """Process outgoing telegram."""
            if self.xknx.knxip_interface is not None:
                await self.xknx.knxip_interface.send_telegram(telegram)
            else:
                self.xknx.logger.warning("No KNXIP interface defined")

        self._out_cb = self.register_telegram_cb(_out_callback)

    async def stop(self):
        """Stop processing."""
        if self._out_cb is not None:
            self.unregister_telegram_cb(self._out_cb)
            self._out_cb = None
        await super().stop()
