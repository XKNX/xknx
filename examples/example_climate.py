"""Example for Climate device."""
import asyncio

from xknx import XKNX
from xknx.devices import Climate


async def main():
    """Connect to KNX/IP and read the state of a Climate device."""
    xknx = XKNX()
    await xknx.start()

    climate = Climate(
        xknx,
        'TestClimate',
        group_address_temperature='6/2/1')
    await climate.sync()

    # Will print out state of climate including current temperature:
    print(climate)

    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
