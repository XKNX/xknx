import asyncio
from xknx import XKNX, Light

async def main():
    xknx = XKNX()
    await xknx.start()
    light = Light(xknx,
                  name='TestLight',
                  group_address_switch='1/0/9')
    light.set_on()
    await asyncio.sleep(2)
    light.set_off()
    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
