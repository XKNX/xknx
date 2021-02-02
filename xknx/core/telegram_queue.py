"""
Module for queing telegrams.

When a device wants to sends a telegram to the KNX bus, it has to queue it to the TelegramQueue within XKNX.

The underlaying KNXIPInterface will poll the queue and send the packets to the correct KNX/IP abstraction (Tunneling or Routing).

You may register callbacks to be notified if a telegram was pushed to the queue.
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Awaitable, Callable, List, Optional, Tuple

from xknx.exceptions import CommunicationError, XKNXException
from xknx.telegram import AddressFilter, GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite

if TYPE_CHECKING:
    from xknx.xknx import XKNX

    AsyncTelegramCallback = Callable[[Telegram], Awaitable[None]]

logger = logging.getLogger("xknx.log")
telegram_logger = logging.getLogger("xknx.telegram")


class TelegramQueue:
    """Class for telegram queue."""

    class Callback:
        """Callback class for handling telegram received callbacks."""

        # pylint: disable=too-few-public-methods

        def __init__(
            self,
            callback: "AsyncTelegramCallback",
            address_filters: Optional[List[AddressFilter]] = None,
            group_addresses: Optional[List[GroupAddress]] = None,
        ):
            """Initialize Callback class."""
            self.callback = callback
            self._match_all = address_filters is None and group_addresses is None
            self.address_filters = [] if address_filters is None else address_filters
            self.group_addresses = [] if group_addresses is None else group_addresses

        def is_within_filter(self, telegram: Telegram) -> bool:
            """Test if callback is filtering for group address."""
            if self._match_all:
                return True
            if isinstance(telegram.destination_address, GroupAddress):
                for address_filter in self.address_filters:
                    if address_filter.match(telegram.destination_address):
                        return True
                for group_address in self.group_addresses:
                    if telegram.destination_address == group_address:
                        return True
            return False

    def __init__(self, xknx: "XKNX"):
        """Initialize TelegramQueue class."""
        self.xknx = xknx
        self.telegram_received_cbs: List[TelegramQueue.Callback] = []
        self.outgoing_queue: asyncio.Queue[Optional[Telegram]] = asyncio.Queue()
        self._consumer_task: Optional[Awaitable[Tuple[None, None]]] = None

    def register_telegram_received_cb(
        self,
        telegram_received_cb: "AsyncTelegramCallback",
        address_filters: Optional[List[AddressFilter]] = None,
        group_addresses: Optional[List[GroupAddress]] = None,
    ) -> Callback:
        """Register callback for a telegram beeing received from KNX bus."""
        callback = TelegramQueue.Callback(
            telegram_received_cb,
            address_filters=address_filters,
            group_addresses=group_addresses,
        )
        self.telegram_received_cbs.append(callback)
        return callback

    def unregister_telegram_received_cb(self, telegram_received_cb: Callback) -> None:
        """Unregister callback for a telegram beeing received from KNX bus."""
        self.telegram_received_cbs.remove(telegram_received_cb)

    async def start(self) -> None:
        """Start telegram queue."""
        self._consumer_task = asyncio.gather(
            self._telegram_consumer(), self._outgoing_rate_limiter()
        )

    async def stop(self) -> None:
        """Stop telegram queue."""
        logger.debug("Stopping TelegramQueue")
        # If a None object is pushed to the queue, the queue stops
        await self.xknx.telegrams.put(None)
        if self._consumer_task is not None:
            await self._consumer_task

    async def _telegram_consumer(self) -> None:
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
                logger.error("Error while processing telegram %s", ex)

    async def _outgoing_rate_limiter(self) -> None:
        """Endless loop for processing outgoing telegrams."""
        while True:
            telegram = await self.outgoing_queue.get()
            # Breaking up queue if None is pushed to the queue
            if telegram is None:
                self.outgoing_queue.task_done()
                break

            try:
                await self.process_telegram_outgoing(telegram)
            except CommunicationError as ex:
                if ex.should_log:
                    logger.warning(ex)
            except XKNXException as ex:
                logger.error("Error while processing outgoing telegram %s", ex)
            finally:
                self.outgoing_queue.task_done()
                self.xknx.telegrams.task_done()

            # limit rate to knx bus - defaults to 20 per second
            if self.xknx.rate_limit:
                await asyncio.sleep(1 / self.xknx.rate_limit)

    async def _process_all_telegrams(self) -> None:
        """Process all telegrams being queued. Used in unit tests."""
        while not self.xknx.telegrams.empty():
            try:
                telegram = self.xknx.telegrams.get_nowait()
                if telegram is None:
                    return
                if telegram.direction == TelegramDirection.INCOMING:
                    await self.process_telegram_incoming(telegram)
                elif telegram.direction == TelegramDirection.OUTGOING:
                    await self.process_telegram_outgoing(telegram)
            except XKNXException as ex:
                logger.error("Error while processing telegram %s", ex)
            finally:
                self.xknx.telegrams.task_done()

    async def process_telegram_outgoing(self, telegram: Telegram) -> None:
        """Process outgoing telegram."""
        telegram_logger.debug(telegram)
        if self.xknx.knxip_interface is not None:
            await self.xknx.knxip_interface.send_telegram(telegram)
            if isinstance(telegram.payload, GroupValueWrite):
                await self.xknx.devices.process(telegram)
        else:
            raise CommunicationError("No KNXIP interface defined")

    async def process_telegram_incoming(self, telegram: Telegram) -> None:
        """Process incoming telegram."""
        telegram_logger.debug(telegram)
        for telegram_received_cb in self.telegram_received_cbs:
            if telegram_received_cb.is_within_filter(telegram):
                await telegram_received_cb.callback(telegram)
        await self.xknx.devices.process(telegram)
