"""Example for Switch device."""
import asyncio

from xknx import XKNX
from xknx.devices import Switch


async def main():
    """Connect to KNX/IP device, switch on outlet, wait 2 seconds and switch of off again."""
    async with XKNX().run() as xknx:
        switch = Switch(xknx,
                        name='TestOutlet',
                        group_address='1/1/11')
        await switch.set_on()
        await asyncio.sleep(2)
        await switch.set_off()


# pylint: disable=invalid-name
asyncio.run(main())
