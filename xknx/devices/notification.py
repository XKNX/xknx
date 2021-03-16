"""Module for managing a notification via KNX."""
import logging
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from xknx.remote_value import GroupAddressesType, RemoteValueString

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Notification(Device):
    """Class for managing a notification."""

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address: Optional[GroupAddressesType] = None,
        group_address_state: Optional[GroupAddressesType] = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize notification class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self._message = RemoteValueString(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            device_name=name,
            feature_name="Message",
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueString]:
        """Iterate the devices RemoteValue classes."""
        yield self._message

    @classmethod
    def from_config(
        cls, xknx: "XKNX", name: str, config: Dict[str, Any]
    ) -> "Notification":
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        group_address_state = config.get("group_address_state")

        return cls(
            xknx,
            name,
            group_address=group_address,
            group_address_state=group_address_state,
        )

    @property
    def message(self) -> Optional[str]:
        """Return the current message."""
        return self._message.value  # type: ignore

    async def set(self, message: str) -> None:
        """Set message."""
        cropped_message = message[:14]
        await self._message.set(cropped_message)

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self._message.process(telegram)

    async def do(self, action: str) -> None:
        """Execute 'do' commands."""
        if action.startswith("message:"):
            await self.set(action[8:])
        else:
            logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<Notification name="{}" message="{}" />'.format(
            self.name, self._message.group_addr_str()
        )
