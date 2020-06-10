"""Example for Climate device."""
import anyio

from xknx import XKNX
from xknx.devices import Climate


async def main():
    """Connect to KNX/IP and read the state of a Climate device."""
    async with XKNX().run() as xknx:
        climate = Climate(
            xknx,
            'TestClimate',
            group_address_temperature='6/2/1')
        await climate.sync()

        # Will print out state of climate including current temperature:
        print(climate)


# pylint: disable=invalid-name
anyio.run(main)
