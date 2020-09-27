"""XKNX is an Asynchronous Python module for reading and writing KNX/IP packets."""
import asyncio
import logging
from logging.handlers import TimedRotatingFileHandler
import os
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

logger = logging.getLogger("xknx.log")


class XKNX:
    """Class for reading and writing KNX/IP packets."""

    # pylint: disable=too-many-instance-attributes

    DEFAULT_ADDRESS = "15.15.250"
    DEFAULT_RATE_LIMIT = 20

    def __init__(
        self,
        config=None,
        own_address=DEFAULT_ADDRESS,
        address_format=GroupAddressType.LONG,
        telegram_received_cb=None,
        device_updated_cb=None,
        rate_limit=DEFAULT_RATE_LIMIT,
        multicast_group=DEFAULT_MCAST_GRP,
        multicast_port=DEFAULT_MCAST_PORT,
        log_directory=None,
        state_updater=False,
        daemon_mode=False,
        connection_config=ConnectionConfig(),
    ):
        """Initialize XKNX class."""
        # pylint: disable=too-many-arguments
        self.devices = Devices()
        self.telegrams = asyncio.Queue()
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
        self.connection_config = connection_config
        self.start_state_updater = state_updater
        self.daemon_mode = daemon_mode
        self.version = VERSION

        if log_directory is not None:
            self.setup_logging(log_directory)

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
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.stop())
            except RuntimeError as exp:
                logger.warning("Could not close loop, reason: %s", exp)

    async def __aenter__(self):
        """Start XKNX from context manager."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        """Stop XKNX from context manager."""
        await self.stop()

    async def start(self):
        """Start XKNX module. Connect to KNX/IP devices and start state updater."""
        self.knxip_interface = KNXIPInterface(
            self, connection_config=self.connection_config
        )
        logger.info(
            "XKNX v%s starting %s connection to KNX bus.",
            VERSION,
            self.connection_config.connection_type.name.lower(),
        )
        await self.knxip_interface.start()
        await self.telegram_queue.start()
        if self.start_state_updater:
            self.state_updater.start()
        self.started.set()
        if self.daemon_mode:
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
            logger.warning("Windows does not support signals")
        else:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(signal.SIGINT, sigint_handler)
        logger.warning("Press Ctrl+C to stop")
        await self.sigint_received.wait()

    @staticmethod
    def setup_logging(log_directory: str):
        """Configure logging to file."""
        if not os.path.isdir(log_directory):
            logger.warning("The provided log directory does not exist.")
            return

        _handler = TimedRotatingFileHandler(
            filename=f"{log_directory}{os.sep}xknx.log",
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        _formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        _handler.setFormatter(_formatter)
        _handler.setLevel(logging.DEBUG)

        for log_namespace in [
            "xknx.log",
            "xknx.knx",
            "xknx.raw_socket",
            "xknx.telegram",
            "xknx.state_updater",
        ]:
            _logger = logging.getLogger(log_namespace)
            _logger.addHandler(_handler)
