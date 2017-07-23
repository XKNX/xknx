import asyncio
from xknx import XKNX, Outlet

async def main():
    xknx = XKNX()
    await xknx.start()
    outlet = Outlet(xknx,
                    name='TestOutlet',
                    group_address='1/1/11')
    outlet.set_on()
    await asyncio.sleep(2)
    outlet.set_off()
    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
