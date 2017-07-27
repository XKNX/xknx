import asyncio
from xknx import XKNX, Climate

async def main():
    xknx = XKNX()
    await xknx.start()

    climate = Climate(
        xknx,
        'TestClimate',
        group_address_temperature='6/2/1')
    await climate.sync()

    # Will print out state of climate including current temperature:
    print(climate)

    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
