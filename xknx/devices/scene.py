"""Module for managing a KNX scene."""
import logging
from typing import TYPE_CHECKING, Any, Iterator, Optional

from xknx.remote_value import RemoteValueSceneNumber

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Scene(Device):
    """Class for managing a scene."""

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address: Optional["GroupAddressableType"] = None,
        scene_number: int = 1,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize Sceneclass."""
        # pylint: disable=too-many-arguments
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

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Any) -> "Scene":
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        scene_number = int(config.get("scene_number"))
        return cls(
            xknx, name=name, group_address=group_address, scene_number=scene_number
        )

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<Scene name="{}" ' 'scene_value="{}" scene_number="{}" />'.format(
            self.name, self.scene_value.group_addr_str(), self.scene_number
        )

    async def run(self) -> None:
        """Activate scene."""
        await self.scene_value.set(self.scene_number)

    async def do(self, action: str) -> None:
        """Execute 'do' commands."""
        if action == "run":
            await self.run()
        else:
            logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )
