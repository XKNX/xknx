"""Module for managing a KNX scene."""
from .device import Device
from .remote_value_scene_number import RemoteValueSceneNumber


class Scene(Device):
    """Class for managing a scene."""

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 scene_number=0,
                 device_updated_cb=None):
        """Initialize Sceneclass."""
        # pylint: disable=too-many-arguments
        super(Scene, self).__init__(xknx, name, device_updated_cb)

        self.scene_value = RemoteValueSceneNumber(
            xknx,
            group_address,
            device_name=self.name,
            after_update_cb=self.after_update)
        self.scene_number = int(scene_number)

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')
        scene_number = \
            int(config.get('scene_number'))
        return cls(
            xknx,
            name=name,
            group_address=group_address,
            scene_number=scene_number)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.scene_value.has_group_address(group_address)

    def __str__(self):
        """Return object as readable string."""
        return '<Scene name="{0}" ' \
               'scene_value="{1}" scene_number="{2}" />' \
            .format(
                self.name,
                self.scene_value.group_addr_str(),
                self.scene_number)

    async def run(self):
        """Move cover down."""
        await self.scene_value.set(self.scene_number)

    async def do(self, action):
        """Execute 'do' commands."""
        if action == "run":
            await self.run()
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return []

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
