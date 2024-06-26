"""Example for daemon mode within XKNX."""

import asyncio

from xknx import XKNX
from xknx.devices import Device, Switch


def device_updated_cb(device: Device) -> None:
    """Do something with the updated device."""
    print(f"Callback received from {device.name}")


async def main() -> None:
    """Connect to KNX/IP device and listen if a switch was updated via KNX bus."""
    xknx = XKNX(device_updated_cb=device_updated_cb, daemon_mode=True)
    xknx.devices.async_add(Switch(xknx, name="TestOutlet", group_address="1/1/11"))
    await xknx.start()
    # Wait until Ctrl-C was pressed
    await xknx.stop()


asyncio.run(main())
