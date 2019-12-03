"""
Module for sending and receiving arbitrary payloads from the KNX bus.

The module will
* ... send the payload to the selected address.
* ... register a callback for receiving telegrams within telegram queue.
* ... check if received telegrams have the correct type address.
* ... store the received telegram for further processing.
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Optional, Type, Union

from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import APCI

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class PayloadReader:
    """Class for sending a request and waiting for a response on the KNX bus."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        xknx: "XKNX",
        address: Union[GroupAddress, IndividualAddress],
        timeout_in_seconds: int = 1,
    ) -> None:
        """Initialize PayloadReader class."""
        self.xknx = xknx
        self.address = address
        self.timeout_in_seconds = timeout_in_seconds

        self.response_received_or_timeout = asyncio.Event()
        self.success = False
        self.timeout_handle: Optional[asyncio.TimerHandle] = None
        self.received_telegram: Optional[Telegram] = None

    def reset(self) -> None:
        """Reset reader for next send."""
        self.response_received_or_timeout = asyncio.Event()
        self.success = False
        self.timeout_handle = None
        self.received_telegram = None

    async def send(
        self, payload: APCI, response_class: Optional[Type[APCI]] = None
    ) -> Optional[APCI]:
        """Send group read and wait for response."""
        self.reset()

        cb_obj = self.xknx.telegram_queue.register_telegram_received_cb(
            lambda t: self.telegram_received(t, response_class)
        )

        await self.xknx.telegrams.put(
            Telegram(destination_address=self.address, payload=payload)
        )
        await self.start_timeout()
        await self.response_received_or_timeout.wait()
        await self.stop_timeout()

        self.xknx.telegram_queue.unregister_telegram_received_cb(cb_obj)

        if not self.success:
            return None
        if self.received_telegram is None:
            return None
        if not isinstance(self.received_telegram.payload, APCI):
            return None

        return self.received_telegram.payload

    async def telegram_received(
        self, telegram: Telegram, response_class: Optional[Type[APCI]]
    ) -> None:
        """Test if telegram is of correct type and address, then trigger event."""
        if response_class:
            if not isinstance(telegram.payload, response_class):
                return
        if self.address != telegram.source_address:
            return
        self.success = True
        self.received_telegram = telegram
        self.response_received_or_timeout.set()

    def timeout(self) -> None:
        """Handle timeout for not having received expected group response."""
        logger.warning(
            "Error: KNX bus did not respond in time (%s secs) to payload request for: %s",
            self.timeout_in_seconds,
            self.address,
        )
        self.response_received_or_timeout.set()

    async def start_timeout(self) -> None:
        """Start timeout. Register callback for no answer received within timeout."""
        loop = asyncio.get_running_loop()
        self.timeout_handle = loop.call_later(self.timeout_in_seconds, self.timeout)

    async def stop_timeout(self) -> None:
        """Stop timeout."""
        if self.timeout_handle:
            self.timeout_handle.cancel()
