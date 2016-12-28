import threading

class TelegramProcessor(threading.Thread):

    def __init__(self, xknx):
        self.xknx = xknx
        threading.Thread.__init__(self)


    def run(self):
        while True:
            telegram = self.xknx.telegrams.get()
            self.process_telegram(telegram)
            self.xknx.telegrams.task_done()

            if telegram.type == TelegramType.OUTGOING:
                # limit rate to knx bus to 50 per second
                time.sleep(1/50)


    def process_telegram(self,telegram):
        if telegram.type == TelegramType.INCOMING:
            self.process_telegram_incoming(telegram)
        elif telegram.type == TelegramType.OUTGOING:
            self.process_telegram_outgoing(telegram)


    def process_telegram_incoming(self,telegram):
        multicast = Multicast(self.xknx)
        multicast.send(telegram)


    def process_telegram_outgoing(self,telegram):
        try:
            device = self.xknx.devices.device_by_group_address(telegram.group_address)
            device.process(telegram)
            if ( callback ):
                callback(self.xknx, device, telegram)
        except CouldNotResolveAddress as c:
            print(c)


    @staticmethod
    def start_thread(xknx):
        t = TelegramProcessor(xknx)
        t.setDaemon(True)
        t.start()
