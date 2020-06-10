"""Example for internal devices storage."""
import anyio

from xknx import XKNX
from xknx.devices import Switch


async def main():
    """Add test Switch to devices storage and access it by name."""
    async with XKNX().run() as xknx:
        switch = Switch(xknx,
                        name='TestOutlet',
                        group_address='1/1/11')
        xknx.devices.add(switch)

        await xknx.devices["TestOutlet"].set_on()
        await anyio.sleep(2)
        await xknx.devices["TestOutlet"].set_off()

# pylint: disable=invalid-name
anyio.run(main)
