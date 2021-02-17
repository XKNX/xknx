"""
Device is the base class for all implemented devices (e.g. Lights/Switches/Sensors).

It provides basis functionality for reading the state from the KNX bus.
"""
from abc import ABC, abstractmethod
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Iterator, List, Optional

from xknx.remote_value import RemoteValue
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknx.xknx import XKNX

DeviceCallbackType = Callable[["Device"], Awaitable[None]]

logger = logging.getLogger("xknx.log")


class Device(ABC):
    """Base class for devices."""

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize Device class."""
        self.xknx = xknx
        self.name = name
        self.device_updated_cbs: List[DeviceCallbackType] = []
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

        self.xknx.devices.add(self)

    def __del__(self) -> None:
        """Remove Device form Devices."""
        try:
            self.shutdown()
        except ValueError:
            pass

    def shutdown(self) -> None:
        """Prepare for deletion. Remove callbacks and device form Devices vector."""
        self.xknx.devices.remove(self)
        self.device_updated_cbs = []
        for remote_value in self._iter_remote_values():
            remote_value.__del__()

    @abstractmethod
    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        # yield self.remote_value
        # yield from (<list all used RemoteValue instances>)
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
        for device_updated_cb in self.device_updated_cbs:
            # pylint: disable=not-callable
            await device_updated_cb(self)

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

    def has_group_address(self, group_address: GroupAddress) -> bool:
        """Test if device has given group address."""
        for remote_value in self._iter_remote_values():
            if remote_value.has_group_address(group_address):
                return True
        return False

    async def do(self, action: str) -> None:
        """Execute 'do' commands."""
        # pylint: disable=invalid-name
        logger.info(
            "'do()' not implemented for action '%s' of %s",
            action,
            self.__class__.__name__,
        )

    def __eq__(self, other: object) -> bool:
        """Compare for quality."""
        return self.__dict__ == other.__dict__
