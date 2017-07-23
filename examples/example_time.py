import asyncio
from xknx import XKNX, Time

async def main():
    xknx = XKNX()
    await xknx.start()

    time = Time(xknx, "TestTime", group_address='1/2/3')

    # Send time to KNX bus
    await time.sync()

    await xknx.stop()

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
