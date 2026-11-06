"""
Module for reading the value of a specific KNX group address from KNX bus.

The module will
* ... send a group_read to the selected group address.
* ... register a callback for receiving telegrams within telegram queue.
* ... check if received telegrams have the correct group address.
* ... store the received telegram for further processing.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Final

from xknx.telegram import Telegram, TelegramDirection
from xknx.telegram.address import GroupAddress, InternalGroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

# Maximum time to wait for the GroupValueRead to pass the outgoing telegram queue.
# The response timeout only starts once it was actually sent.
MAX_SEND_WAIT_TIME: Final = 10.0


class ValueReader:
    """Class for reading the value of a specific KNX group address from KNX bus."""

    __slots__ = (
        "_timeout",
        "group_address",
        "received_telegram",
        "response_received_event",
        "sent",
        "timeout_in_seconds",
        "xknx",
    )

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddress | InternalGroupAddress,
        timeout_in_seconds: float = 2.0,
    ) -> None:
        """Initialize ValueReader class."""
        self.xknx = xknx
        self.group_address: GroupAddress | InternalGroupAddress = group_address
        self.response_received_event = asyncio.Event()
        self.timeout_in_seconds: float = timeout_in_seconds
        self.received_telegram: Telegram | None = None
        # True once a GroupValueRead for the group address has passed the outgoing telegram queue
        self.sent = False
        self._timeout: asyncio.Timeout | None = None

    async def read(self) -> Telegram | None:
        """Send group read and wait for response."""
        cb_obj = self.xknx.telegram_queue.register_telegram_received_cb(
            self.telegram_received,
            group_addresses=[self.group_address],
            match_for_outgoing=True,
        )
        self.send_group_read()

        try:
            # The GroupValueRead may wait in the outgoing queue behind other telegrams.
            # The response timeout is armed in `telegram_received()` when it has been
            # sent; until then only the send wait time bounds the read.
            async with asyncio.timeout(MAX_SEND_WAIT_TIME) as self._timeout:
                await self.response_received_event.wait()
        except TimeoutError:
            if self.sent:
                logger.warning(
                    "Error: KNX bus did not respond in time (%s secs) to GroupValueRead request for: %s",
                    self.timeout_in_seconds,
                    self.group_address,
                )
            else:
                logger.warning(
                    "Error: GroupValueRead request for %s could not be sent in time (%s secs)",
                    self.group_address,
                    MAX_SEND_WAIT_TIME,
                )
        else:
            return self.received_telegram
        finally:
            self._timeout = None
            # cleanup to not leave callbacks (for asyncio.CancelledError)
            self.xknx.telegram_queue.unregister_telegram_received_cb(cb_obj)

        return None

    def send_group_read(self) -> None:
        """Send group read."""
        telegram = Telegram(
            destination_address=self.group_address,
            payload=GroupValueRead(),
            source_address=self.xknx.current_address,
        )
        self.xknx.telegrams.put_nowait(telegram)

    def telegram_received(self, telegram: Telegram) -> None:
        """Test if telegram has correct group address and trigger event."""
        if telegram.destination_address != self.group_address:
            return
        if telegram.direction is TelegramDirection.OUTGOING and isinstance(
            telegram.payload, GroupValueRead
        ):
            # the GroupValueRead was sent - start the response timeout now
            self.sent = True
            if self._timeout is not None and not self._timeout.expired():
                self._timeout.reschedule(
                    asyncio.get_running_loop().time() + self.timeout_in_seconds
                )
            return
        if isinstance(telegram.payload, GroupValueResponse | GroupValueWrite):
            self.received_telegram = telegram
            self.response_received_event.set()
