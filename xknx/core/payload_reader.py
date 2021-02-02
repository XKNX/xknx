"""
Module for sending and receiving arbitrary payloads from the KNX bus.

The module will
* ... send the payload to the selected address.
* ... register a callback for receiving telegrams within telegram queue.
* ... check if received telegrams have the correct type and address.
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

    def __init__(
        self,
        xknx: "XKNX",
        address: Union[GroupAddress, IndividualAddress],
        timeout_in_seconds: float = 2.0,
    ) -> None:
        """Initialize PayloadReader class."""
        self.xknx = xknx
        self.address = address
        self.response_received_or_timeout = asyncio.Event()
        self.success: bool = False
        self.timeout_in_seconds = timeout_in_seconds
        self.received_payload: Optional[APCI] = None

    def reset(self) -> None:
        """Reset reader for next send."""
        self.response_received_or_timeout = asyncio.Event()
        self.success = False
        self.received_payload = None

    async def send(
        self, payload: APCI, response_class: Optional[Type[APCI]] = None
    ) -> Optional[APCI]:
        """
        Send APCI payload request and wait for a response.

        An optional `response_class` can be specified to wait for a specific
        APCI response payload.
        """
        self.reset()

        cb_obj = self.xknx.telegram_queue.register_telegram_received_cb(
            lambda t: self.telegram_received(t, response_class)
        )
        await self.send_telegram(payload)

        try:
            await asyncio.wait_for(
                self.response_received_or_timeout.wait(),
                timeout=self.timeout_in_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Error: KNX bus did not respond in time (%s secs) to payload request for: %s",
                self.timeout_in_seconds,
                self.address,
            )
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.xknx.telegram_queue.unregister_telegram_received_cb(cb_obj)

        if not self.success:
            return None
        if self.received_payload is None:
            return None
        return self.received_payload

    async def send_telegram(self, payload: APCI) -> None:
        """Send the telegram."""
        await self.xknx.telegrams.put(
            Telegram(destination_address=self.address, payload=payload)
        )

    async def telegram_received(
        self, telegram: Telegram, response_class: Optional[Type[APCI]] = None
    ) -> None:
        """Test if telegram is of correct type and address, then trigger event."""
        if self.address != telegram.source_address:
            return
        if not isinstance(telegram.payload, APCI):
            return
        if response_class:
            if not isinstance(telegram.payload, response_class):
                return
        self.success = True
        self.received_payload = telegram.payload
        self.response_received_or_timeout.set()
