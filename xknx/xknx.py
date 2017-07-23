import asyncio
import signal
from xknx.knx import Address
from xknx.io import KNXIPInterface, ConnectionConfig
from .devices import Devices
from .globals import Globals
from .telegram_queue import  TelegramQueue
from .config import Config

class XKNX:
    # pylint: disable=too-many-instance-attributes

    def __init__(self,
                 config=None,
                 loop=None,
                 own_address=None,
                 telegram_received_cb=None,
                 device_updated_cb=None):
        # pylint: disable=too-many-arguments
        self.globals = Globals()
        self.devices = Devices()
        self.telegrams = asyncio.Queue()
        self.loop = loop or asyncio.get_event_loop()
        #self.loop.set_debug(True)
        self.sigint_received = asyncio.Event()
        self.telegram_queue = TelegramQueue(self)
        self.state_updater = None
        self.knxip_interface = None
        self.started = False

        if config is not None:
            Config(self).read(config)

        if own_address is not None:
            self.globals.own_address = Address(own_address)

        if telegram_received_cb is not None:
            self.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        if device_updated_cb is not None:
            self.devices.register_device_updated_cb(device_updated_cb)


    def __del__(self):
        if self.started:
            try:
                task = asyncio.Task(self.stop())
                self.loop.run_until_complete(task)
            except RuntimeError as exp:
                print("Could not close loop, reason: ", exp)


    @asyncio.coroutine
    def start(self,
              state_updater=False,
              daemon_mode=False,
              connection_config=ConnectionConfig()):

        self.knxip_interface = KNXIPInterface(self,connection_config=connection_config)
        yield from self.knxip_interface.start()

        yield from self.telegram_queue.start()

        if state_updater:
            from .stateupdater import StateUpdater
            self.state_updater = StateUpdater(self)
            yield from self.state_updater.start()

        if daemon_mode:
            yield from self.loop_until_sigint()

        self.started = True

    @asyncio.coroutine
    def join(self):
        """ Wait until all telegrams were processed """
        yield from self.telegrams.join()


    def stop_knxip_interface_if_exists(self):
        if self.knxip_interface is not None:
            yield from self.knxip_interface.stop()
            self.knxip_interface = None


    @asyncio.coroutine
    def stop(self):
        yield from self.join()
        yield from self.telegram_queue.stop()
        yield from self.stop_knxip_interface_if_exists()
        self.started = False

    @asyncio.coroutine
    def loop_until_sigint(self):
        def sigint_handler():
            self.sigint_received.set()
        self.loop.add_signal_handler(signal.SIGINT, sigint_handler)
        print('Press Ctrl+C to stop')
        yield from self.sigint_received.wait()
