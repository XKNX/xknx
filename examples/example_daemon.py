"""Example for daemon mode within XKNX."""
import asyncio

from xknx import XKNX
from xknx.devices import Switch


async def device_updated_cb(device):
    """Do something with the updated device."""
    print("Callback received from {0}".format(device.name))


async def main():
    """Connect to KNX/IP device and listen if a switch was updated via KNX bus."""
    xknx = XKNX(device_updated_cb=device_updated_cb)
    switch = Switch(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    xknx.devices.add(switch)

    # Wait until Ctrl-C was pressed
    await xknx.start(daemon_mode=True)

    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
