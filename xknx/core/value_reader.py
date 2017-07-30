"""
Module for reading the value of a specific KNX group address from KNX bus.

The module will
* ... send a group_read to the selected gruop address.
* ... register a callback for receiving telegrams within telegram queue.
* ... check if received telegrams have the correct group address.
* ... store the received telegram for further processing.
"""

import asyncio

from xknx.knx import Telegram, TelegramType

class ValueReader:
    """Class for reading the value of a specific KNX group address from KNX bus."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, xknx, group_address, timeout_in_seconds=1):
        """Initialize ValueReader class."""
        self.xknx = xknx
        self.group_address = group_address
        self.response_received_or_timeout = asyncio.Event()
        self.success = False
        self.timeout_in_seconds = timeout_in_seconds
        self.timeout_callback = None
        self.timeout_handle = None
        self.received_telegram = None

    @asyncio.coroutine
    def read(self):
        """Send group read and wait for response."""
        @asyncio.coroutine
        def telegram_received_callback(telegram):
            """Callback for having received a telegram."""
            return self.telegram_received(telegram)

        self.xknx.telegram_queue.register_telegram_received_cb(
            telegram_received_callback)

        yield from self.send_group_read()
        yield from self.start_timeout()
        yield from self.response_received_or_timeout.wait()
        yield from self.stop_timeout()

        self.xknx.telegram_queue.unregister_telegram_received_cb(
            telegram_received_callback)

        if not self.success:
            return None
        return self.received_telegram


    @asyncio.coroutine
    def send_group_read(self):
        """Send group read."""
        telegram = Telegram(self.group_address, TelegramType.GROUP_READ)
        yield from self.xknx.telegrams.put(telegram)

    def telegram_received(self, telegram):
        """Callback for having received a telegram. Check if group addresses match."""
        if self.group_address == telegram.group_address:
            self.success = True
            self.received_telegram = telegram
            self.response_received_or_timeout.set()
            return True
        return False

    def timeout(self):
        """Callback for handling timeout."""
        self.response_received_or_timeout.set()

    @asyncio.coroutine
    def start_timeout(self):
        """Start timeout. Register callback for no answer received within timeout."""
        self.timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self.timeout)

    @asyncio.coroutine
    def stop_timeout(self):
        """Stop timeout."""
        self.timeout_handle.cancel()
