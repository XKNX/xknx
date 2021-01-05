"""
Module for managing a fan via KNX.

It provides functionality for

* setting fan to specific speed
* reading the current speed from KNX bus.
"""
import logging
from typing import TYPE_CHECKING, Any, Iterator, Optional

from xknx.remote_value import RemoteValueScaling

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Fan(Device):
    """Class for managing a fan."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address_speed: Optional["GroupAddressableType"] = None,
        group_address_speed_state: Optional["GroupAddressableType"] = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize fan class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.speed = RemoteValueScaling(
            xknx,
            group_address_speed,
            group_address_speed_state,
            device_name=self.name,
            feature_name="Speed",
            after_update_cb=self.after_update,
            range_from=0,
            range_to=100,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValueScaling]:
        """Iterate the devices RemoteValue classes."""
        yield self.speed

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Any) -> "Fan":
        """Initialize object from configuration structure."""
        group_address_speed = config.get("group_address_speed")
        group_address_speed_state = config.get("group_address_speed_state")

        return cls(
            xknx,
            name,
            group_address_speed=group_address_speed,
            group_address_speed_state=group_address_speed_state,
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<Fan name="{}" ' 'speed="{}" />'.format(
            self.name, self.speed.group_addr_str()
        )

    async def set_speed(self, speed: int) -> None:
        """Set the fan to a desginated speed."""
        await self.speed.set(speed)

    async def do(self, action: str) -> None:
        """Execute 'do' commands."""
        if action.startswith("speed:"):
            await self.set_speed(int(action[6:]))
        else:
            logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.speed.process(telegram)

    @property
    def current_speed(self) -> Optional[int]:
        """Return current speed of fan."""
        return self.speed.value  # type: ignore
