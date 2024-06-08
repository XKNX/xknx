"""Example for reading the state from the KNX bus."""

import asyncio

from xknx import XKNX
from xknx.devices import Light


async def main() -> None:
    """Connect to KNX/IP bus and read the state of a Light device."""
    async with XKNX() as xknx:
        light = Light(
            xknx,
            name="TestLight2",
            group_address_switch="1/0/12",
            group_address_brightness="1/0/14",
        )
        xknx.devices.async_add(light)

        await light.set_brightness(80)
        # Will do a GroupValueRead for both addresses and block until a result is received
        await light.sync(wait_for_result=True)
        print(light)


asyncio.run(main())
