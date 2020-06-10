"""Example for DateTime device."""
import anyio

from xknx import XKNX
from xknx.devices import DateTime, DateTimeBroadcastType


async def main():
    """Connect to KNX/IP device and broadcast time."""
    xknx = XKNX()
    datetime = DateTime(xknx, 'TimeTest', group_address='1/2/3', broadcast_type=DateTimeBroadcastType.TIME)
    xknx.devices.add(datetime)
    print("Sending time to KNX bus every hour")
    async with xknx.run(state_updater=True):
        while True:
            anyio.sleep(99999)

# pylint: disable=invalid-name
anyio.run(main)
