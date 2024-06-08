"""Example for switching a light on and off."""

import asyncio

from xknx import XKNX
from xknx.devices import Light


async def main() -> None:
    """Connect to KNX/IP bus, switch on light, wait 2 seconds and switch of off again."""
    xknx = XKNX()
    await xknx.start()
    light = Light(xknx, name="TestLight", group_address_switch="1/0/9")
    xknx.devices.async_add(light)

    await light.set_on()
    await asyncio.sleep(2)
    await light.set_off()
    await xknx.stop()


asyncio.run(main())
