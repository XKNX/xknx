"""Example for switching a light on and off."""
import asyncio

from xknx import XKNX
from xknx.devices import Scene


async def main():
    """Connect to KNX/IP bus and run scene."""
    async with XKNX().run() as xknx:
        scene = Scene(
            xknx,
            name='Romantic',
            group_address='7/0/9',
            scene_number=23)
        await scene.run()


asyncio.run(main())
