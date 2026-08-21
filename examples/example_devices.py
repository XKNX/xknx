"""Example for internal devices storage."""

import asyncio

from xknx import XKNX
from xknx.devices import Switch


async def main() -> None:
    """Add test Switch to devices storage and use it."""
    xknx = XKNX()
    await xknx.start()
    switch = Switch(xknx, name="TestOutlet", group_address="1/1/11")
    xknx.devices.async_add(switch)

    # devices registered in the storage receive telegrams from the bus
    assert switch in xknx.devices
    for device in xknx.devices:
        print(device)

    await switch.set_on()
    await asyncio.sleep(2)
    await switch.set_off()

    xknx.devices.async_remove(switch)
    await xknx.stop()


asyncio.run(main())
