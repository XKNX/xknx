import asyncio
from xknx import XKNX, Thermostat

async def main():
    xknx = XKNX()
    await xknx.start()

    thermostat = Thermostat(
        xknx,
        'TestThermostat',
        group_address_temperature='6/2/1')
    await thermostat.sync()

    # Will print out state of thermostat including current temperature:
    print(thermostat)

    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
