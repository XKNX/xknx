"""Example for switching a light on and off."""
import anyio

from xknx import XKNX
from xknx.devices import Light


async def main():
    """Connect to KNX/IP bus, slowly dimm on light, set it off again afterwards."""
    async with XKNX().run() as xknx:

        light = Light(xknx,
                      name='TestLight2',
                      group_address_switch='1/0/12',
                      group_address_brightness='1/0/14')

        for i in [0, 31, 63, 95, 127, 159, 191, 223, 255]:
            await light.set_brightness(i)
            await anyio.sleep(1)

        await light.set_off()


anyio.run(main)
