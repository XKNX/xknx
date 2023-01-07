"""XKNX is an Asynchronous Python module for reading and writing KNX/IP packets."""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import signal
from sys import platform
from types import TracebackType
from typing import Callable

from xknx.cemi import CEMIHandler
from xknx.core import (
    ConnectionManager,
    TaskRegistry,
    TelegramQueue,
    XknxConnectionState,
)
from xknx.core.state_updater import StateUpdater, TrackerOptionType
from xknx.devices import Device, Devices
from xknx.io import (
    DEFAULT_MCAST_GRP,
    DEFAULT_MCAST_PORT,
    ConnectionConfig,
    knx_interface_factory,
)
from xknx.management import Management
from xknx.telegram import GroupAddress, GroupAddressType, IndividualAddress, Telegram

from .__version__ import __version__ as VERSION

logger = logging.getLogger("xknx.log")


class XKNX:
    """Class for reading and writing KNX/IP packets."""

    def __init__(
        self,
        address_format: GroupAddressType = GroupAddressType.LONG,
        telegram_received_cb: Callable[[Telegram], Awaitable[None]] | None = None,
        device_updated_cb: Callable[[Device], Awaitable[None]] | None = None,
        connection_state_changed_cb: Callable[[XknxConnectionState], Awaitable[None]]
        | None = None,
        rate_limit: int = 0,
        multicast_group: str = DEFAULT_MCAST_GRP,
        multicast_port: int = DEFAULT_MCAST_PORT,
        log_directory: str | None = None,
        state_updater: TrackerOptionType = False,
        daemon_mode: bool = False,
        connection_config: ConnectionConfig | None = None,
    ) -> None:
        """Initialize XKNX class."""
        self.connection_manager = ConnectionManager()
        self.devices = Devices()
        self.knxip_interface = knx_interface_factory(
            self, connection_config=connection_config or ConnectionConfig()
        )
        self.management = Management(self)
        self.telegrams: asyncio.Queue[Telegram | None] = asyncio.Queue()
        self.telegram_queue = TelegramQueue(self)
        self.cemi_handler = CEMIHandler(self)
        self.state_updater = StateUpdater(self, default_tracker_option=state_updater)
        self.task_registry = TaskRegistry(self)

        self.current_address = IndividualAddress(0)
        self.daemon_mode = daemon_mode
        self.multicast_group = multicast_group
        self.multicast_port = multicast_port
        self.rate_limit = rate_limit
        self.sigint_received = asyncio.Event()
        self.started = asyncio.Event()
        self.version = VERSION

        GroupAddress.address_format = address_format  # for global string representation
        if log_directory is not None:
            self.setup_logging(log_directory)

        if telegram_received_cb is not None:
            self.telegram_queue.register_telegram_received_cb(telegram_received_cb)

        if device_updated_cb is not None:
            self.devices.register_device_updated_cb(device_updated_cb)

        if connection_state_changed_cb is not None:
            self.connection_manager.register_connection_state_changed_cb(
                connection_state_changed_cb
            )

    def __del__(self) -> None:
        """Destructor. Cleaning up if this was not done before."""
        if self.started.is_set():
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.stop())
            except RuntimeError as exp:
                logger.warning("Could not close loop, reason: %s", exp)

    async def __aenter__(self) -> "XKNX":
        """Start XKNX from context manager."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop XKNX from context manager."""
        await self.stop()

    async def start(self) -> None:
        """Start XKNX module. Connect to KNX/IP devices and start state updater."""
        if self.knxip_interface.connection_config.threaded:
            await self.connection_manager.register_loop()
        self.task_registry.start()
        logger.info(
            "XKNX v%s starting %s connection to KNX bus.",
            VERSION,
            self.knxip_interface.connection_config.connection_type.name.lower(),
        )
        await self.knxip_interface.start()
        await self.telegram_queue.start()
        self.state_updater.start()
        self.started.set()
        if self.daemon_mode:
            await self.loop_until_sigint()

    async def join(self) -> None:
        """Wait until all telegrams were processed."""
        await self.telegrams.join()

    async def stop(self) -> None:
        """Stop XKNX module."""
        self.task_registry.stop()
        self.state_updater.stop()
        await self.join()
        await self.telegram_queue.stop()
        await self.knxip_interface.stop()
        self.started.clear()

    async def loop_until_sigint(self) -> None:
        """Loop until Crtl-C was pressed."""

        def sigint_handler() -> None:
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
    def setup_logging(log_directory: str) -> None:
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
            "xknx.cemi",
            "xknx.log",
            "xknx.knx",
            "xknx.raw_socket",
            "xknx.telegram",
            "xknx.state_updater",
        ]:
            _logger = logging.getLogger(log_namespace)
            _logger.addHandler(_handler)
