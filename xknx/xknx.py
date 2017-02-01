import asyncio
import signal
from .devices import Devices
from .globals import Globals

class XKNX:
    # pylint: disable=too-many-instance-attributes

    START_TELEGRAM_QUEUE = 0x01
    START_MULITCAST_DAEMON = 0x02
    START_STATE_UPDATER = 0x04

    START_DEFAULT = START_TELEGRAM_QUEUE | \
                    START_MULITCAST_DAEMON | \
                    START_STATE_UPDATER


    def __init__(self, loop=None):
        self.globals = Globals()
        self.devices = Devices()
        self.telegrams = asyncio.Queue()
        self.loop = loop or asyncio.get_event_loop()
        self.sigint_recieved = asyncio.Event()
        self.telegram_queue = None
        self.knxip_interface = None
        self.state_updater = None


    def start(self,
              daemon_mode=False,
              telegram_received_callback=None):

        task = asyncio.Task(
            self.async_start(
                daemon_mode,
                telegram_received_callback=telegram_received_callback))

        self.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_start(self,
                    daemon_mode=False,
                    start=START_DEFAULT,
                    telegram_received_callback=None):
        from .telegram_queue import  TelegramQueue
        from .stateupdater import StateUpdater
        from xknx.io.async import KNXIPInterface

        if start & XKNX.START_TELEGRAM_QUEUE:
            self.telegram_queue = TelegramQueue(
                self,
                telegram_received_callback)
            yield from self.telegram_queue.start()

        if start & XKNX.START_MULITCAST_DAEMON:
            self.knxip_interface = KNXIPInterface(self)
            yield from self.knxip_interface.start()

        if start & XKNX.START_STATE_UPDATER:
            self.state_updater = StateUpdater(self)
            yield from self.state_updater.start()

        if daemon_mode:
            yield from self.loop_until_sigint()


    def join(self):
        """ Wait until all telegrams were processed """
        self.telegrams.join()


    def stop(self):
        self.join()
        #self.loop.stop()
        print("Shutdown process ...")


    @asyncio.coroutine
    def loop_until_sigint(self):

        def sigint_handler():
            self.sigint_recieved.set()

        self.loop.add_signal_handler(signal.SIGINT, sigint_handler)

        print('Press Ctrl+C to stop')
        yield from self.sigint_recieved.wait()
