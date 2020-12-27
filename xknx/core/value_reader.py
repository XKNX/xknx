"""
Module for reading the value of a specific KNX group address from KNX bus.

The module will
* ... send a group_read to the selected gruop address.
* ... register a callback for receiving telegrams within telegram queue.
* ... check if received telegrams have the correct group address.
* ... store the received telegram for further processing.
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Optional

from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class ValueReader:
    """Class for reading the value of a specific KNX group address from KNX bus."""

    def __init__(
        self, xknx: "XKNX", group_address: GroupAddress, timeout_in_seconds: float = 2.0
    ):
        """Initialize ValueReader class."""
        self.xknx = xknx
        self.group_address: GroupAddress = group_address
        self.response_received_or_timeout = asyncio.Event()
        self.success: bool = False
        self.timeout_in_seconds: float = timeout_in_seconds
        self.received_telegram: Optional[Telegram] = None

    async def read(self) -> Optional[Telegram]:
        """Send group read and wait for response."""
        cb_obj = self.xknx.telegram_queue.register_telegram_received_cb(
            self.telegram_received
        )
        await self.send_group_read()

        try:
            await asyncio.wait_for(
                self.response_received_or_timeout.wait(),
                timeout=self.timeout_in_seconds,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Error: KNX bus did not respond in time (%s secs) to GroupValueRead request for: %s",
                self.timeout_in_seconds,
                self.group_address,
            )
        finally:
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.xknx.telegram_queue.unregister_telegram_received_cb(cb_obj)

        if not self.success:
            return None
        return self.received_telegram

    async def send_group_read(self) -> None:
        """Send group read."""
        telegram = Telegram(
            destination_address=self.group_address, payload=GroupValueRead()
        )
        await self.xknx.telegrams.put(telegram)

    async def telegram_received(self, telegram: Telegram) -> None:
        """Test if telegram has correct group address and trigger event."""
        if telegram.destination_address == self.group_address and isinstance(
            telegram.payload, (GroupValueResponse, GroupValueWrite)
        ):
            self.success = True
            self.received_telegram = telegram
            self.response_received_or_timeout.set()
