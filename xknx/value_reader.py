import asyncio

from xknx.knx import Telegram, TelegramType

class ValueReader:
    # pylint: disable=too-many-instance-attributes

    def __init__(self, xknx, group_address, timeout_in_seconds=1):
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

        def telegram_received_callback(telegram):
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
        telegram = Telegram(self.group_address, TelegramType.GROUP_READ)
        yield from self.xknx.telegrams.put(telegram)

    def telegram_received(self, telegram):
        if self.group_address == telegram.group_address:
            self.success = True
            self.received_telegram = telegram
            self.response_received_or_timeout.set()
            return True
        return False

    def timeout(self):
        self.response_received_or_timeout.set()

    @asyncio.coroutine
    def start_timeout(self):
        self.timeout_handle = self.xknx.loop.call_later(
            self.timeout_in_seconds, self.timeout)

    @asyncio.coroutine
    def stop_timeout(self):
        self.timeout_handle.cancel()
