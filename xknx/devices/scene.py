"""Module for managing a KNX scene."""
from __future__ import annotations

from collections.abc import Iterator
import logging
from typing import TYPE_CHECKING

from xknx.remote_value import GroupAddressesType, RemoteValueSceneNumber

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Scene(Device):
    """Class for managing a scene."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType | None = None,
        scene_number: int = 1,
        device_updated_cb: DeviceCallbackType[Scene] | None = None,
    ):
        """Initialize Sceneclass."""
        super().__init__(xknx, name, device_updated_cb)

        # TODO: state_updater: disable for scene number per default?
        self.scene_value = RemoteValueSceneNumber(
            xknx,
            group_address=group_address,
            device_name=self.name,
            feature_name="Scene number",
            after_update_cb=self.after_update,
        )
        self.scene_number = int(scene_number)

    def _iter_remote_values(self) -> Iterator[RemoteValueSceneNumber]:
        """Iterate the devices RemoteValue classes."""
        yield self.scene_value

    async def run(self) -> None:
        """Activate scene."""
        await self.scene_value.set(self.scene_number)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Scene name="{self.name}" '
            f"scene_value={self.scene_value.group_addr_str()} "
            f'scene_number="{self.scene_number}" />'
        )
