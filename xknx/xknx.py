"""XKNX is an Asynchronous Python module for reading and writing KNX/IP packets."""
import asyncio
import logging
import signal
from sys import platform

from xknx.core import Config, StateUpdater, TelegramQueue
from xknx.devices import Devices
from xknx.io import (
    DEFAULT_MCAST_GRP,
    DEFAULT_MCAST_PORT,
    ConnectionConfig,
    KNXIPInterface,
)
from xknx.telegram import GroupAddressType, PhysicalAddress

from .__version__ import __version__ as VERSION


class XKNX:
    """Class for reading and writing KNX/IP packets."""

    # pylint: disable=too-many-instance-attributes

    DEFAULT_ADDRESS = "15.15.250"
    DEFAULT_RATE_LIMIT = 20

    def __init__(
        self,
        config=None,
        loop=None,
        own_address=DEFAULT_ADDRESS,
        address_format=GroupAddressType.LONG,
        telegram_received_cb=None,
        device_updated_cb=None,
        rate_limit=DEFAULT_RATE_LIMIT,
        multicast_group=DEFAULT_MCAST_GRP,
        multicast_port=DEFAULT_MCAST_PORT,
    ):
        """Initialize XKNX class."""
        # pylint: disable=too-many-arguments
        self.devices = Devices()
        self.telegrams = asyncio.Queue()
        self.loop = loop or asyncio.get_event_loop()
        self.sigint_received = asyncio.Event()
        self.telegram_queue = TelegramQueue(self)
        self.state_updater = StateUpdater(self)
        self.knxip_interface = None
        self.started = asyncio.Event()
        self.address_format = address_format
        self.own_address = PhysicalAddress(own_address)
        self.rate_limit = rate_limit
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.logger = logging.getLogger("xknx.log")
        self.knx_logger = logging.getLogger("xknx.knx")
        self.telegram_logger = logging.getLogger("xknx.telegram")
        self.raw_socket_logger = logging.getLogger("xknx.raw_socket")
        self.connection_config = None
        self.version = VERSION

        if config is not None:
            Config(self).read(config)

        if telegram_received_cb is not None:
            self.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        if device_updated_cb is not None:
            self.devices.register_device_updated_cb(device_updated_cb)

    def __del__(self):
        """Destructor. Cleaning up if this was not done before."""
        if self.started.is_set():
            try:
                task = self.loop.create_task(self.stop())
                self.loop.run_until_complete(task)
            except RuntimeError as exp:
                self.logger.warning("Could not close loop, reason: %s", exp)

    async def start(
        self, state_updater=False, daemon_mode=False, connection_config=None
    ):
        """Start XKNX module. Connect to KNX/IP devices and start state updater."""
        if connection_config is None:
            if self.connection_config is None:
                connection_config = ConnectionConfig()
            else:
                connection_config = self.connection_config
        self.knxip_interface = KNXIPInterface(self, connection_config=connection_config)
        self.logger.info(
            "XKNX v%s starting %s connection to KNX bus.",
            VERSION,
            connection_config.connection_type.name.lower(),
        )
        await self.knxip_interface.start()
        await self.telegram_queue.start()
        if state_updater:
            self.state_updater.start()
        self.started.set()
        if daemon_mode:
            await self.loop_until_sigint()

    async def join(self):
        """Wait until all telegrams were processed."""
        await self.telegrams.join()

    async def _stop_knxip_interface_if_exists(self):
        """Stop KNXIPInterface if initialized."""
        if self.knxip_interface is not None:
            await self.knxip_interface.stop()
            self.knxip_interface = None

    async def stop(self):
        """Stop XKNX module."""
        self.state_updater.stop()
        await self.join()
        await self.telegram_queue.stop()
        await self._stop_knxip_interface_if_exists()
        self.started.clear()

    async def loop_until_sigint(self):
        """Loop until Crtl-C was pressed."""

        def sigint_handler():
            """End loop."""
            self.sigint_received.set()

        if platform == "win32":
            self.logger.warning("Windows does not support signals")
        else:
            self.loop.add_signal_handler(signal.SIGINT, sigint_handler)
        self.logger.warning("Press Ctrl+C to stop")
        await self.sigint_received.wait()
