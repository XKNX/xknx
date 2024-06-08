"""Example for internal devices storage."""

import asyncio

from xknx import XKNX
from xknx.devices import Switch


async def main() -> None:
    """Add test Switch to devices storage and access it by name."""
    xknx = XKNX()
    await xknx.start()
    switch = Switch(xknx, name="TestOutlet", group_address="1/1/11")
    xknx.devices.async_add(switch)

    await xknx.devices["TestOutlet"].set_on()
    await asyncio.sleep(2)
    await xknx.devices["TestOutlet"].set_off()
    await xknx.stop()


asyncio.run(main())
