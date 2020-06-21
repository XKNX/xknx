"""Example for DateTime device."""
import asyncio

from xknx import XKNX
from xknx.devices import DateTime


async def main():
    """Connect to KNX/IP device and broadcast time."""
    xknx = XKNX()
    datetime = DateTime(xknx, 'TimeTest', group_address='1/2/3', broadcast_type="time")
    xknx.devices.add(datetime)
    print("Sending time to KNX bus every hour")
    await xknx.start(daemon_mode=True)
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
