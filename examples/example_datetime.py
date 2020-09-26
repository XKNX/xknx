"""Example for DateTime device."""
import asyncio

from xknx import XKNX
from xknx.devices import DateTime


async def main():
    """Connect to KNX/IP device and broadcast time."""
    xknx = XKNX()
    DateTime(xknx, "TimeTest", group_address="1/2/3", broadcast_type="time")
    print("Sending time to KNX bus every hour")
    await xknx.start(daemon_mode=True)
    await xknx.stop()


asyncio.run(main())
