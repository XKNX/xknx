import asyncio
from xknx import XKNX, Outlet

async def main():
    xknx = XKNX(config='xknx.yaml')

    for device in xknx.devices:
        print(device)

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
