import asyncio
from xknx import XKNX, Switch


def device_updated_cb(device):
    print("Callback received from {0}".format(device.name))


async def main():
    xknx = XKNX(device_updated_cb=device_updated_cb)
    switch = Switch(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    xknx.devices.add(switch)

    await xknx.start(daemon_mode=True)

    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
