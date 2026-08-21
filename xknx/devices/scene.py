"""Module for managing a KNX scene."""

from __future__ import annotations

from collections.abc import Iterator
import logging
from typing import TYPE_CHECKING

from xknx.dpt import SceneControl
from xknx.remote_value import GroupAddressesType, RemoteValueSceneControl

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import GroupValueTelegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Scene(Device):
    """Class for managing a scene."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address: GroupAddressesType = None,
        scene_number: int = 1,
        device_updated_cb: DeviceCallbackType[Scene] | None = None,
    ) -> None:
        """Initialize Sceneclass."""
        super().__init__(xknx, name, device_updated_cb)

        self.scene_value = RemoteValueSceneControl(
            xknx,
            group_address=group_address,
            device_name=self.name,
            feature_name="Scene control",
            after_update_cb=self._scene_control_from_rv,
        )
        self.scene_number = int(scene_number)
        self._learn_requested = False

    def _iter_remote_values(self) -> Iterator[RemoteValueSceneControl]:
        """Iterate the devices RemoteValue classes."""
        yield self.scene_value

    @property
    def learn_requested(self) -> bool:
        """Return if the last telegram for this scene requested storing it."""
        return self._learn_requested

    async def run(self) -> None:
        """Activate scene."""
        self.scene_value.set(SceneControl(self.scene_number, learn=False))

    async def learn(self) -> None:
        """Let actuators store their current state as this scene."""
        self.scene_value.set(SceneControl(self.scene_number, learn=True))

    def process_group_write(self, telegram: GroupValueTelegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        self.scene_value.process(telegram, always_callback=True)

    def _scene_control_from_rv(self, scene_control: SceneControl) -> None:
        """Check the scene control from RemoteValue (Callback)."""
        # scene_value holds every scene number seen on the group address, so
        # callbacks are only called - and `learn_requested` is only updated -
        # for telegrams of this devices scene number
        if scene_control.scene_number != self.scene_number:
            return
        self._learn_requested = scene_control.learn
        self.after_update()

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Scene name="{self.name}" '
            f"scene_value={self.scene_value.group_addr_str()} "
            f'scene_number="{self.scene_number}" />'
        )
