import queue
from .devices import Devices
from .globals import Globals
import signal

class XKNX:

    START_TELEGRAM_PROCESSOR = 0x01
    START_MULITCAST_DAEMON   = 0x02
    START_STATE_UPDATER      = 0x04

    START_DEFAULT = START_TELEGRAM_PROCESSOR | \
                    START_MULITCAST_DAEMON | \
                    START_STATE_UPDATER

    def __init__(self):
        self.globals = Globals()
        self.devices = Devices()
        self.telegrams = queue.Queue()


    def start(self,
            daemon_mode = False,
            start = START_DEFAULT,
            telegram_received_callback = None):
        from .multicast import MulticastDaemon
        from .telegram_processor import  TelegramProcessor
        from .stateupdater import StateUpdater

        if start & XKNX.START_TELEGRAM_PROCESSOR:
            TelegramProcessor.start_thread(self, telegram_received_callback)
        if start & XKNX.START_MULITCAST_DAEMON:
            MulticastDaemon.start_thread(self)
        if start & XKNX.START_STATE_UPDATER:
            StateUpdater.start_thread(self, 10)

        if daemon_mode:
            self.loop_until_sigint()


    def join(self):
        """ Wait until all telegrams were processed """
        self.telegrams.join()


    def stop(self):
        self.join()
        print("Process stopped")


    def loop_until_sigint(self):
        def sigint_handler(signal, frame):
            self.stop()

        signal.signal(signal.SIGINT, sigint_handler)
        print('Press Ctrl+C')
        signal.pause()
