"""
Module for queueing telegrams addressed to group addresses.

When a device wants to send a telegram to the KNX bus, it has to queue it to the
TelegramQueue within XKNX. The telegram will be forwarded to the local CEMIHandler and
processed in xknx-Devices.
You may register callbacks to be notified if a telegram was pushed to the queue.

Telegrams addressed to IndividualAddresses are not processed by this queue.
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
import logging
from typing import TYPE_CHECKING, Callable

from xknx.exceptions import CommunicationError, XKNXException
from xknx.telegram import AddressFilter, Telegram, TelegramDirection
from xknx.telegram.address import GroupAddress, InternalGroupAddress

if TYPE_CHECKING:
    from xknx.xknx import XKNX

    AsyncTelegramCallback = Callable[[Telegram], Awaitable[None]]

logger = logging.getLogger("xknx.log")
telegram_logger = logging.getLogger("xknx.telegram")


class TelegramQueue:
    """Class for telegram queue."""

    class Callback:
        """Callback class for handling telegram received callbacks."""

        def __init__(
            self,
            callback: AsyncTelegramCallback,
            address_filters: list[AddressFilter] | None = None,
            group_addresses: list[GroupAddress | InternalGroupAddress] | None = None,
            match_for_outgoing_telegrams: bool = False,
        ):
            """Initialize Callback class."""
            self.callback = callback
            self._match_all = address_filters is None and group_addresses is None
            self._match_outgoing = match_for_outgoing_telegrams
            self.address_filters = [] if address_filters is None else address_filters
            self.group_addresses = [] if group_addresses is None else group_addresses

        def is_within_filter(self, telegram: Telegram) -> bool:
            """Test if callback is filtering for group address."""
            if (
                not self._match_outgoing
                and telegram.direction == TelegramDirection.OUTGOING
            ):
                return False
            if self._match_all:
                return True
            if isinstance(
                telegram.destination_address, (GroupAddress, InternalGroupAddress)
            ):
                for address_filter in self.address_filters:
                    if address_filter.match(telegram.destination_address):
                        return True
                for group_address in self.group_addresses:
                    if telegram.destination_address == group_address:
                        return True
            return False

    def __init__(self, xknx: XKNX):
        """Initialize TelegramQueue class."""
        self.xknx = xknx
        self.telegram_received_cbs: list[TelegramQueue.Callback] = []
        self.outgoing_queue: asyncio.Queue[Telegram | None] = asyncio.Queue()
        self._consumer_task: Awaitable[tuple[None, None]] | None = None
        self._rate_limiter: asyncio.Task[None] | None = None

    def register_telegram_received_cb(
        self,
        telegram_received_cb: AsyncTelegramCallback,
        address_filters: list[AddressFilter] | None = None,
        group_addresses: list[GroupAddress | InternalGroupAddress] | None = None,
        match_for_outgoing: bool = False,
    ) -> TelegramQueue.Callback:
        """Register callback for a telegram being received from KNX bus."""
        callback = TelegramQueue.Callback(
            telegram_received_cb,
            address_filters=address_filters,
            group_addresses=group_addresses,
            match_for_outgoing_telegrams=match_for_outgoing,
        )
        self.telegram_received_cbs.append(callback)
        return callback

    def unregister_telegram_received_cb(
        self, telegram_received_cb: TelegramQueue.Callback
    ) -> None:
        """Unregister callback for a telegram being received from KNX bus."""
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

            if telegram.direction == TelegramDirection.INCOMING:
                try:
                    await self.process_telegram_incoming(telegram)
                except XKNXException:
                    logger.exception(
                        "Unexpected xknx error while processing incoming telegram %s",
                        telegram,
                    )
                except Exception:  # pylint: disable=broad-except
                    # prevent the parser Task from stalling when unexpected errors occur
                    logger.exception(
                        "Unexpected error while processing incoming telegram %s",
                        telegram,
                    )
                finally:
                    self.xknx.telegrams.task_done()
            elif telegram.direction == TelegramDirection.OUTGOING:
                self.outgoing_queue.put_nowait(telegram)
                # self.xknx.telegrams.task_done() for outgoing is called in _outgoing_rate_limiter.

    async def _outgoing_rate_limiter(self) -> None:
        """Endless loop for processing outgoing telegrams."""
        while True:
            telegram = await self.outgoing_queue.get()
            # Breaking up queue if None is pushed to the queue
            if telegram is None:
                self.outgoing_queue.task_done()
                if self._rate_limiter:
                    self._rate_limiter.cancel()
                break

            # limit rate to knx bus - defaults to 20 per second
            if self.xknx.rate_limit and not isinstance(
                telegram.destination_address, InternalGroupAddress
            ):
                if self._rate_limiter is not None:
                    await self._rate_limiter
                self._rate_limiter = asyncio.create_task(
                    asyncio.sleep(1 / self.xknx.rate_limit)
                )

            try:
                await self.process_telegram_outgoing(telegram)
            except CommunicationError as ex:
                if ex.should_log:
                    logger.warning(ex)
            except XKNXException as ex:
                logger.error("Error while processing outgoing telegram %s", ex)
            except Exception:  # pylint: disable=broad-except
                # prevent the sender Task from stalling when unexpected errors occur (eg. ValueError from creating KNXIPFrames)
                logger.exception(
                    "Unexpected error while processing outgoing telegram %s", telegram
                )
            finally:
                self.outgoing_queue.task_done()
                self.xknx.telegrams.task_done()

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
        if not isinstance(telegram.destination_address, InternalGroupAddress):
            # raises CommunicationError when interface is not connected
            await self.xknx.cemi_handler.send_telegram(telegram)

        await self.xknx.devices.process(telegram)
        await self._run_telegram_received_cbs(telegram)

    async def process_telegram_incoming(self, telegram: Telegram) -> None:
        """Process incoming telegram."""
        telegram_logger.debug(telegram)
        await self._run_telegram_received_cbs(telegram)
        await self.xknx.devices.process(telegram)

    async def _run_telegram_received_cbs(self, telegram: Telegram) -> None:
        """Run registered callbacks. Don't propagate exceptions."""
        callbacks = [
            cb.callback(telegram)
            for cb in self.telegram_received_cbs
            if cb.is_within_filter(telegram)
        ]
        try:
            await asyncio.gather(*callbacks)
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Unexpected error while processing telegram_received_cb for %s",
                telegram,
            )
