"""Example for Climate device."""

import asyncio

from xknx import XKNX
from xknx.devices import Climate


async def main():
    """Connect to KNX/IP and read the state of a Climate device."""
    xknx = XKNX()
    async with xknx:
        climate = Climate(xknx, "TestClimate", group_address_temperature="6/2/1")
        await climate.sync(wait_for_result=True)
        # Will print out state of climate including current temperature:
        print(climate)


asyncio.run(main())
