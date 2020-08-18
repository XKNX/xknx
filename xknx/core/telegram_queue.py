"""
Module for queing telegrams.

When a device wants to sends a telegram to the KNX bus, it has to queue it to the TelegramQueue within XKNX.

The underlaying KNXIPInterface will poll the queue and send the packets to the correct KNX/IP abstraction (Tunneling or Routing).

You may register callbacks to be notified if a telegram was pushed to the queue.
"""
import asyncio

from xknx.exceptions import XKNXException
from xknx.telegram import TelegramDirection


class TelegramQueue():
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
            if self.address_filters is None:
                return True
            for address_filter in self.address_filters:
                if address_filter.match(telegram.group_address):
                    return True
            return False

    def __init__(self, xknx):
        """Initialize TelegramQueue class."""
        self.xknx = xknx
        self.telegram_received_cbs = []
        self.outgoing_queue = asyncio.Queue()
        self._consumer_task = None

    def register_telegram_received_cb(self, telegram_received_cb, address_filters=None):
        """Register callback for a telegram beeing received from KNX bus."""
        callback = TelegramQueue.Callback(telegram_received_cb, address_filters)
        self.telegram_received_cbs.append(callback)
        return callback

    def unregister_telegram_received_cb(self, telegram_received_cb):
        """Unregister callback for a telegram beeing received from KNX bus."""
        self.telegram_received_cbs.remove(telegram_received_cb)

    async def start(self):
        """Start telegram queue."""
        self._consumer_task = asyncio.gather(
            self._telegram_consumer(),
            self._outgoing_rate_limiter()
        )

    async def stop(self):
        """Stop telegram queue."""
        self.xknx.logger.debug("Stopping TelegramQueue")
        # If a None object is pushed to the queue, the queue stops
        await self.xknx.telegrams.put(None)
        await self._consumer_task

    async def _telegram_consumer(self):
        """Endless loop for processing telegrams."""
        while True:
            telegram = await self.xknx.telegrams.get()
            # Breaking up queue if None is pushed to the queue
            if telegram is None:
                self.outgoing_queue.put_nowait(None)
                await self.outgoing_queue.join()
                self.xknx.telegrams.task_done()
                break

            try:
                if telegram.direction == TelegramDirection.INCOMING:
                    await self.process_telegram_incoming(telegram)
                    self.xknx.telegrams.task_done()
                elif telegram.direction == TelegramDirection.OUTGOING:
                    self.outgoing_queue.put_nowait(telegram)
                    # self.xknx.telegrams.task_done() for outgoing is called in _outgoing_rate_limiter.
            except XKNXException as ex:
                self.xknx.logger.error("Error while processing telegram %s", ex)

    async def _outgoing_rate_limiter(self):
        """Endless loop for processing outgoing telegrams."""
        while True:
            telegram = await self.outgoing_queue.get()
            # Breaking up queue if None is pushed to the queue
            if telegram is None:
                self.outgoing_queue.task_done()
                break

            try:
                await self.process_telegram_outgoing(telegram)
            except XKNXException as ex:
                self.xknx.logger.error("Error while processing outgoing telegram %s", ex)
            finally:
                self.outgoing_queue.task_done()
                self.xknx.telegrams.task_done()

            # limit rate to knx bus - defaults to 20 per second
            if self.xknx.rate_limit:
                await asyncio.sleep(1 / self.xknx.rate_limit)

    async def _process_all_telegrams(self):
        """Process all telegrams being queued. Used in unit tests."""
        while not self.xknx.telegrams.empty():
            try:
                telegram = self.xknx.telegrams.get_nowait()
                if telegram.direction == TelegramDirection.INCOMING:
                    await self.process_telegram_incoming(telegram)
                elif telegram.direction == TelegramDirection.OUTGOING:
                    await self.process_telegram_outgoing(telegram)
            except XKNXException as ex:
                self.xknx.logger.error("Error while processing telegram %s", ex)
            finally:
                self.xknx.telegrams.task_done()

    async def process_telegram_outgoing(self, telegram):
        """Process outgoing telegram."""
        self.xknx.telegram_logger.debug(telegram)
        if self.xknx.knxip_interface is not None:
            await self.xknx.knxip_interface.send_telegram(telegram)
        else:
            self.xknx.logger.warning("No KNXIP interface defined")

    async def process_telegram_incoming(self, telegram):
        """Process incoming telegram."""
        self.xknx.telegram_logger.debug(telegram)
        processed = False
        for telegram_received_cb in self.telegram_received_cbs:
            if telegram_received_cb.is_within_filter(telegram):
                ret = await telegram_received_cb.callback(telegram)
                if ret:
                    processed = True

        if not processed:
            for device in self.xknx.devices.devices_by_group_address(
                    telegram.group_address):
                await device.process(telegram)
