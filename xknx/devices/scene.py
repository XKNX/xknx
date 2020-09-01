"""Module for managing a KNX scene."""
from xknx.remote_value import RemoteValueSceneNumber

from .device import Device


class Scene(Device):
    """Class for managing a scene."""

    def __init__(
        self, xknx, name, group_address=None, scene_number=1, device_updated_cb=None
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

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        yield self.scene_value

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        scene_number = int(config.get("scene_number"))
        return cls(
            xknx, name=name, group_address=group_address, scene_number=scene_number
        )

    def __str__(self):
        """Return object as readable string."""
        return '<Scene name="{}" ' 'scene_value="{}" scene_number="{}" />'.format(
            self.name, self.scene_value.group_addr_str(), self.scene_number
        )

    async def run(self):
        """Activate scene."""
        await self.scene_value.set(self.scene_number)

    async def do(self, action):
        """Execute 'do' commands."""
        if action == "run":
            await self.run()
        else:
            self.xknx.logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )
