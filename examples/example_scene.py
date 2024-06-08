"""Example for switching a light on and off."""

import asyncio

from xknx import XKNX
from xknx.devices import Scene


async def main() -> None:
    """Connect to KNX/IP bus and run scene."""
    async with XKNX() as xknx:
        scene = Scene(xknx, name="Romantic", group_address="7/0/9", scene_number=23)
        xknx.devices.async_add(scene)

        await scene.run()


asyncio.run(main())
