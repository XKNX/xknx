"""
Module for reading the value of a specific KNX group address from KNX bus.

The module will
* ... send a group_read to the selected gruop address.
* ... register a callback for receiving telegrams within telegram queue.
* ... check if received telegrams have the correct group address.
* ... store the received telegram for further processing.
"""

import anyio

from xknx.telegram import Telegram, TelegramType


class ValueReader:
    """Class for reading the value of a specific KNX group address from KNX bus."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, xknx, group_address, timeout_in_seconds=1):
        """Initialize ValueReader class."""
        self.xknx = xknx
        self.group_address = group_address
        self.timeout_in_seconds = timeout_in_seconds
        self.received_telegram = None

    async def read(self):
        """Send group read and wait for response."""
        with self.xknx.telegram_receiver() as recv:
            await self.send_group_read()
            try:
                # anyio buglet
                async with anyio.fail_after(self.timeout_in_seconds or 0.01):
                    async for telegram in recv:
                        if await self.telegram_received(telegram):
                            return telegram
            except TimeoutError:
                self.xknx.logger.warning("Error: KNX bus did not respond in time to GroupValueRead request for: %s",
                                        self.group_address)
        return None

    async def send_group_read(self):
        """Send group read."""
        telegram = Telegram(self.group_address, TelegramType.GROUP_READ)
        await self.xknx.telegrams.put(telegram)

    async def telegram_received(self, telegram):
        """Test if telegram has correct group address and trigger event."""
        if telegram.telegramtype not in (
                TelegramType.GROUP_RESPONSE, TelegramType.GROUP_WRITE):
            return False
        if self.group_address != telegram.group_address:
            return False
        self.received_telegram = telegram
        return True
