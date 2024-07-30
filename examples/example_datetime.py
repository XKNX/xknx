"""Example for Date and Time devices."""

import asyncio

from xknx import XKNX
from xknx.devices import TimeDevice


async def main() -> None:
    """Connect to KNX/IP device and broadcast time."""
    xknx = XKNX(daemon_mode=True)
    xknx.devices.async_add(TimeDevice(xknx, "TimeTest", group_address="1/2/3"))
    print("Sending time to KNX bus every hour")
    await xknx.start()
    await xknx.stop()


asyncio.run(main())
