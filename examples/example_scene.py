"""Example for activating a scene and for reacting to scenes called on the bus."""

import asyncio

from xknx import XKNX
from xknx.devices import Scene


def scene_updated_cb(scene: Scene) -> None:
    """Handle a telegram for the scene number of this device."""
    if scene.learn_requested:
        # a learn telegram tells actuators to store their current state
        print(f"Storing current state as scene {scene.scene_number}")
    else:
        print(f"Restoring state of scene {scene.scene_number}")


async def main() -> None:
    """Connect to KNX/IP bus, call a scene and listen for scenes called by others."""
    async with XKNX() as xknx:
        scene = Scene(
            xknx,
            name="Romantic",
            group_address="7/0/9",
            scene_number=23,
            device_updated_cb=scene_updated_cb,
        )
        xknx.devices.async_add(scene)

        # `scene.learn()` would ask the actuators to store their current state
        # as this scene instead of restoring it
        await scene.run()

        # listen for scene telegrams from the bus
        await asyncio.sleep(10)


asyncio.run(main())
