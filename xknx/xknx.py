"""XKNX is an Asynchronous Python module for reading and writing KNX/IP packets."""
import anyio
import logging
import signal
try:
    from contextlib import asynccontextmanager
except ImportError:
    from async_generator import asynccontextmanager

from xknx.core import Config, TelegramQueueIn, TelegramQueueOut
from xknx.devices import Devices
from xknx.io import ConnectionConfig, KNXIPInterface
from xknx.telegram import GroupAddressType, PhysicalAddress

import sniffio

from .__version__ import __version__ as VERSION


class XKNX:
    """Class for reading and writing KNX/IP packets."""

    # pylint: disable=too-many-instance-attributes

    DEFAULT_ADDRESS = '15.15.250'
    DEFAULT_RATE_LIMIT = 20

    def __init__(self,
                 config=None,
                 loop=None,  # pylint: disable=unused-argument
                 own_address=None,
                 address_format=GroupAddressType.LONG,
                 telegram_received_cb=None,
                 device_updated_cb=None,
                 rate_limit=DEFAULT_RATE_LIMIT):
        """Initialize XKNX class."""
        # pylint: disable=too-many-arguments
        self.devices = Devices()
        self.telegrams_in = TelegramQueueIn(self)
        self.telegrams_out = TelegramQueueOut(self)
        self.state_updater = None
        self.knxip_interface = None
        self.started = False
        self.address_format = address_format
        if own_address is None:
            own_address=PhysicalAddress(self.DEFAULT_ADDRESS)
        self.own_address = own_address
        self.rate_limit = rate_limit
        self.logger = logging.getLogger('xknx.log')
        self.knx_logger = logging.getLogger('xknx.knx')
        self.telegram_logger = logging.getLogger('xknx.telegram')
        self.raw_socket_logger = logging.getLogger('xknx.raw_socket')
        self.connection_config = None
        self.version = VERSION

        self.task_group = None
        self._stopped = None
        self._main_task = None

        if config is not None:
            Config(self).read(config)

        if telegram_received_cb is not None:
            self.telegrams_in.register_telegram_cb(telegram_received_cb)

        if device_updated_cb is not None:
            self.devices.register_device_updated_cb(device_updated_cb)

    @asynccontextmanager
    async def run(self, state_updater=False, connection_config=None):
        """Async context manager for XKNX. Connect to KNX/IP devices and start state updater."""
        async with anyio.create_task_group() as tg:
            self.task_group = tg
            self._stopped = anyio.create_event()

            try:
                await self._start(state_updater=state_updater,
                                  connection_config=connection_config)
                yield self
                await tg.cancel_scope.cancel()
            finally:
                async with anyio.move_on_after(2, shield=True):
                    await self._stop()
                    await self._stopped.set()

    async def start(self,
                    state_updater=False,
                    daemon_mode=False,
                    connection_config=None):
        """Start XKNX module. Connect to KNX/IP devices and start state updater.

        This is a compatibility method which starts a separate task for XKNX.
        You might want to use `async with xknx.run()` instead.
        """
        if daemon_mode:
            async with self.run(state_updater=state_updater, connection_config=connection_config):
                await self.loop_until_sigint()
            return
        if sniffio.current_async_library() != "asyncio":
            raise RuntimeError("You need to use a context manager.")

        import asyncio
        self._stopped = anyio.create_event()
        self._main_task = asyncio.create_task(self._run(state_updater=state_updater,
                                                        connection_config=connection_config))

    async def _run(self, **kw):
        async with self.run(**kw):
            while True:
                await anyio.sleep(9999)

    async def _start(self,
                     state_updater=False,
                     connection_config=None):
        if connection_config is None:
            if self.connection_config is None:
                connection_config = ConnectionConfig()
            else:
                connection_config = self.connection_config
        self.knxip_interface = KNXIPInterface(self, connection_config=connection_config)
        self.logger.info('XKNX v%s starting %s connection to KNX bus.',
                         VERSION, connection_config.connection_type.name.lower())
        await self.knxip_interface.start()
        await self.telegrams_in.start()
        await self.telegrams_out.start()

        if state_updater:
            # pylint: disable=import-outside-toplevel
            from xknx.core import StateUpdater
            self.state_updater = StateUpdater(self)
            await self.state_updater.start()

        self.started = True

    def telegram_receiver(self, *a):
        """Shortcut to `TelegramQueueIn.receiver`."""
        return self.telegrams_in.receiver(*a)

    async def spawn(self, p, *a, **k):
        """Start a task.

        Returns a cancel scope.
        """
        scope = None

        async def _spawn(evt, p, a, k):
            nonlocal scope
            async with anyio.open_cancel_scope() as scope:  # pylint: disable=unused-variable
                await evt.set()
                await p(*a, **k)

        evt = anyio.create_event()
        await self.task_group.spawn(_spawn, evt, p, a, k)
        await evt.wait()
        return scope

    async def join(self):
        """Wait until all telegrams are processed."""
        while self.telegrams_in.qsize():
            await anyio.sleep(0.01)
        while self.telegrams_out.qsize():
            await anyio.sleep(0.01)

    async def _stop_knxip_interface_if_exists(self):
        """Stop KNXIPInterface if initialized."""
        if self.knxip_interface is not None:
            await self.knxip_interface.stop()
            self.knxip_interface = None

    async def stop(self, wait=True):
        """Stop XKNX module."""
        if self._main_task is not None:
            self._main_task.cancel()
        if self.task_group is not None:
            await self.task_group.cancel_scope.cancel()
        if wait:
            await self._stopped.wait()

    async def _stop(self):
        if self.state_updater:
            await self.state_updater.stop()
        await self.join()
        await self.telegrams_in.stop()
        await self.telegrams_out.stop()
        await self._stop_knxip_interface_if_exists()
        self.started = False

    async def loop_until_sigint(self):
        """Loop until Crtl-C was pressed."""
        self.logger.warning('Press Ctrl+C to stop')
        async with anyio.receive_signals(signal.SIGINT) as sig:
            async for _ in sig:
                await self.stop(wait=False)
                self.logger.warning('Terminating.')
                break
