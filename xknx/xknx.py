import asyncio
import signal
from xknx.knx import Address
from xknx.io.async import KNXIPInterface
from .devices import Devices
from .globals import Globals
from .telegram_queue import  TelegramQueue

class XKNX:
    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 loop=None,
                 own_address=None,
                 start=True,
                 state_updater=False,
                 daemon_mode=False,
                 telegram_received_callback=None):

        self.globals = Globals()
        self.devices = Devices()
        self.telegrams = asyncio.Queue()
        self.loop = loop or asyncio.get_event_loop()
        #self.loop.set_debug(True)
        self.sigint_recieved = asyncio.Event()
        self.telegram_queue = TelegramQueue(self)
        self.state_updater = None
        self.knxip_interface = None

        if own_address is not None:
            self.globals.own_address = Address(own_address)

        if start:
            self.start(
                state_updater=state_updater,
                daemon_mode=daemon_mode,
                telegram_received_callback=telegram_received_callback)


    def __del__(self):
        try:
            task = asyncio.Task(
                self.async_stop())
            self.loop.run_until_complete(task)
        except:
            pass


    def start(self,
              state_updater=False,
              daemon_mode=False,
              telegram_received_callback=None):
        task = asyncio.Task(
            self.async_start(
                state_updater=state_updater,
                daemon_mode=daemon_mode,
                telegram_received_callback=telegram_received_callback))
        self.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_start(self,
                    state_updater=False,
                    daemon_mode=False,
                    telegram_received_callback=None):


        self.knxip_interface = KNXIPInterface(self)
        yield from self.knxip_interface.start()

        if telegram_received_callback is not None:
            self.telegram_queue.telegram_received_callback =\
                telegram_received_callback
        yield from self.telegram_queue.start()

        if state_updater:
            from .stateupdater import StateUpdater
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


    def stop_knxip_interface_if_exists(self):
        if self.knxip_interface is not None:
            yield from self.knxip_interface.async_stop()
            self.knxip_interface = None


    def stop(self):
        task = asyncio.Task(self.async_stop())
        self.loop.run_until_complete(task)


    @asyncio.coroutine
    def async_stop(self):
        yield from self.join()
        yield from self.telegram_queue.stop()
        yield from self.stop_knxip_interface_if_exists()

    @asyncio.coroutine
    def loop_until_sigint(self):

        def sigint_handler():
            self.sigint_recieved.set()

        self.loop.add_signal_handler(signal.SIGINT, sigint_handler)

        print('Press Ctrl+C to stop')
        yield from self.sigint_recieved.wait()

        yield from self.async_stop()
