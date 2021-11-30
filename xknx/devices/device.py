"""
Device is the base class for all implemented devices (e.g. Lights/Switches/Sensors).

It provides basis functionality for reading the state from the KNX bus.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterator

from xknx.core import Task, XknxConnectionState
from xknx.remote_value import RemoteValue
from xknx.telegram import Telegram
from xknx.telegram.address import DeviceGroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknx.xknx import XKNX

DeviceCallbackType = Callable[["Device"], Awaitable[None]]

logger = logging.getLogger("xknx.log")


class Device(ABC):
    """Base class for devices."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        device_updated_cb: DeviceCallbackType | None = None,
        sync_state: bool | int | float | str = True,
    ):
        """Initialize Device class."""
        self.xknx = xknx
        self.name = name
        self._available = False
        self._connected = False
        self.sync_state = sync_state
        self.device_updated_cbs: list[DeviceCallbackType] = []
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

        self._task: Task | None = None
        self.xknx.devices.add(self)

    def _start_state_initialization_listener(
        self, register_callbacks: bool = True
    ) -> None:
        """Create task for state initialization."""
        if register_callbacks:
            self.xknx.connection_manager.register_connection_state_changed_cb(
                self.connection_state_change_callback
            )
            self._connected = (
                self.xknx.connection_manager.state == XknxConnectionState.CONNECTED
            )

        self._task = self.xknx.task_registry.register(
            str(id(self)), self.listen_for_state_initialization()
        )
        self._task.start()

    async def connection_state_change_callback(
        self, state: XknxConnectionState
    ) -> None:
        """Start and stop StateUpdater via connection state update."""
        await self._update_state_updaters(state)

        if self._connected and state is not XknxConnectionState.CONNECTED:
            self._connected = False
            self._available = False
            await self.after_update()
        elif state is XknxConnectionState.CONNECTED:
            #  after update called after state initialisation
            self._connected = True
            #  restart state initialisation after updating state updater internally
            self._start_state_initialization_listener(False)

    async def _update_state_updaters(self, state: XknxConnectionState) -> None:
        """Update the state updaters."""
        #  update all the state updaters belonging to this device
        if tasks := [
            remote_value.state_updater.connection_state_change_callback(state)
            for remote_value in self._iter_remote_values()
        ]:
            await asyncio.gather(*tasks)

    @property
    def available(self) -> bool:
        """Return if the device is connected and available."""
        return self._available and self._connected

    def __del__(self) -> None:
        """Remove Device form Devices."""
        try:
            self.shutdown()
        except (ValueError, AttributeError):
            pass

    async def listen_for_state_initialization(self) -> None:
        """Listen for state initialization for the state updater."""
        for remote_value in self._iter_remote_values():
            await remote_value.state_updater.initialized.wait()

        self._available = True
        logger.debug(
            "Device state is now initialized for %s - marking as available",
            self,
        )
        await self.after_update()

    def shutdown(self) -> None:
        """Prepare for deletion. Remove callbacks and device form Devices vector."""
        self.xknx.devices.remove(self)
        self.xknx.connection_manager.unregister_connection_state_changed_cb(
            self.connection_state_change_callback
        )
        self.device_updated_cbs = []
        for remote_value in self._iter_remote_values():
            remote_value.__del__()
        for task in self._iter_tasks():
            if task:
                self.xknx.task_registry.unregister(task.name)

        if self._task:
            self.xknx.task_registry.unregister(self._task.name)

    @abstractmethod
    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        # yield self.remote_value
        # yield from (<list all used RemoteValue instances>)
        yield from ()

    def _iter_tasks(self) -> Iterator[Task | None]:  # pylint: disable=no-self-use
        """Iterate the device tasks."""
        yield from ()

    def register_device_updated_cb(self, device_updated_cb: DeviceCallbackType) -> None:
        """Register device updated callback."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(
        self, device_updated_cb: DeviceCallbackType
    ) -> None:
        """Unregister device updated callback."""
        self.device_updated_cbs.remove(device_updated_cb)

    async def after_update(self) -> None:
        """Execute callbacks after internal state has been changed."""
        try:
            await asyncio.gather(*[cb(self) for cb in self.device_updated_cbs])
        except Exception:  # pylint: disable=broad-except
            logger.exception(
                "Unexpected error while processing device_updated_cb for %s",
                self,
            )

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read states of device from KNX bus."""
        for remote_value in self._iter_remote_values():
            await remote_value.read_state(wait_for_result=wait_for_result)

    async def process(self, telegram: Telegram) -> None:
        """Process incoming telegram."""
        if isinstance(telegram.payload, GroupValueWrite):
            await self.process_group_write(telegram)
        elif isinstance(telegram.payload, GroupValueResponse):
            await self.process_group_response(telegram)
        elif isinstance(telegram.payload, GroupValueRead):
            await self.process_group_read(telegram)

    async def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GroupValueRead telegrams."""
        # The default is, that devices don't answer to group reads

    async def process_group_response(self, telegram: Telegram) -> None:
        """Process incoming GroupValueResponse telegrams."""
        # Per default mapped to group write.
        await self.process_group_write(telegram)

    async def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming GroupValueWrite telegrams."""
        # The default is, that devices don't process group writes

    def get_name(self) -> str:
        """Return name of device."""
        return self.name

    def has_group_address(self, group_address: DeviceGroupAddress) -> bool:
        """Test if device has given group address."""
        for remote_value in self._iter_remote_values():
            if remote_value.has_group_address(group_address):
                return True
        return False

    def __eq__(self, other: object) -> bool:
        """Compare for quality."""
        return self.__dict__ == other.__dict__
