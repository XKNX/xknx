import asyncio
from xknx import XKNX, Switch

async def main():
    xknx = XKNX()
    await xknx.start()
    switch = Switch(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    xknx.devices.add(switch)

    xknx.devices["TestOutlet"].set_on()
    await asyncio.sleep(2)
    xknx.devices["TestOutlet"].set_off()
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
