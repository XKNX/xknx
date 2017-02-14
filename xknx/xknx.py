import asyncio
import signal
from xknx.knx import Address
from xknx.io.async import KNXIPInterface
from .devices import Devices
from .globals import Globals
from .telegram_queue import  TelegramQueue

class XKNX:
    # pylint: disable=too-many-instance-attributes

    START_TELEGRAM_QUEUE = 0x01
    START_MULITCAST_DAEMON = 0x02
    START_STATE_UPDATER = 0x04

    START_DEFAULT = START_TELEGRAM_QUEUE | \
                    START_MULITCAST_DAEMON | \
                    START_STATE_UPDATER


    def __init__(self, loop=None, own_address=None, own_ip=None):
        self.globals = Globals()
        self.devices = Devices()
        self.telegrams = asyncio.Queue()
        self.loop = loop or asyncio.get_event_loop()
        self.sigint_recieved = asyncio.Event()
        self.telegram_queue = TelegramQueue(self)
        self.knxip_interface = KNXIPInterface(self)
        self.state_updater = None

        if own_address is not None:
            self.globals.own_address = Address(own_address)
        if own_ip is not None:
            self.globals.own_ip = own_ip


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
        from .stateupdater import StateUpdater

        if start & XKNX.START_TELEGRAM_QUEUE:
            self.telegram_queue.telegram_received_callback = telegram_received_callback
            yield from self.telegram_queue.start()

        if start & XKNX.START_MULITCAST_DAEMON:
            yield from self.knxip_interface.start()

        if start & XKNX.START_STATE_UPDATER:
            self.state_updater = StateUpdater(self)
            yield from self.state_updater.start()

        if daemon_mode:
            yield from self.loop_until_sigint()

    def process_all_telegrams(self):
        task = asyncio.Task(
            self.telegram_queue.process_all_telegrams())
        self.loop.run_until_complete(task)

    @asyncio.coroutine
    def join(self):
        """ Wait until all telegrams were processed """
        yield from self.telegrams.join()


    @asyncio.coroutine
    def stop(self):
        yield from self.join()
        #self.loop.stop()
        print("Shutdown process ...")


    @asyncio.coroutine
    def loop_until_sigint(self):

        def sigint_handler():
            self.sigint_recieved.set()

        self.loop.add_signal_handler(signal.SIGINT, sigint_handler)

        print('Press Ctrl+C to stop')
        yield from self.sigint_recieved.wait()
