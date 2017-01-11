import threading
import time

from .telegram import TelegramDirection
from .devices import CouldNotResolveAddress
from .multicast import Multicast

class TelegramProcessor(threading.Thread):

    def __init__(self, xknx, telegram_received_callback=None):
        self.xknx = xknx
        self.telegram_received_callback = telegram_received_callback
        threading.Thread.__init__(self)


    def run(self):
        while True:
            telegram = self.xknx.telegrams.get()
            self.process_telegram(telegram)
            self.xknx.telegrams.task_done()
            if telegram.direction == TelegramDirection.OUTGOING:
                # limit rate to knx bus to 20 per second
                time.sleep(1/20)

    def process_telegram(self, telegram):
        try:

            if telegram.direction == TelegramDirection.INCOMING:
                self.process_telegram_incoming(telegram)
            elif telegram.direction == TelegramDirection.OUTGOING:
                self.process_telegram_outgoing(telegram)

        except Exception as exception:
            print("Exceptio while processing telegram:", exception)


    def process_telegram_outgoing(self, telegram):
        multicast = Multicast(self.xknx)
        multicast.send(telegram)


    def process_telegram_incoming(self, telegram):
        device = self.xknx.devices.device_by_group_address(
            telegram.group_address)
        device.process(telegram)
        if self.telegram_received_callback:
            self.telegram_received_callback(self.xknx, device, telegram)


    @staticmethod
    def start_thread(xknx, telegram_received_callback=None):
        telegramprocessor = TelegramProcessor(xknx, telegram_received_callback)
        telegramprocessor.setDaemon(True)
        telegramprocessor.start()
