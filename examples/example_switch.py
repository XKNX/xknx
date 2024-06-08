"""Example for Switch device."""

import asyncio

from xknx import XKNX
from xknx.devices import Switch


async def main() -> None:
    """Connect to KNX/IP device, switch on outlet, wait 2 seconds and switch of off again."""
    xknx = XKNX()
    await xknx.start()
    switch = Switch(xknx, name="TestOutlet", group_address="1/1/11")
    xknx.devices.async_add(switch)
    await switch.set_on()
    await asyncio.sleep(2)
    await switch.set_off()
    await xknx.stop()


asyncio.run(main())
