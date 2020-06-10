"""Example for switching a light on and off."""
import anyio

from xknx import XKNX
from xknx.devices import Light


async def main():
    """Connect to KNX/IP bus, switch on light, wait 2 seconds and switch of off again."""
    async with XKNX().run() as xknx:
        light = Light(xknx,
                    name='TestLight',
                    group_address_switch='1/0/9')
        await light.set_on()
        await anyio.sleep(2)
        await light.set_off()


anyio.run(main)
