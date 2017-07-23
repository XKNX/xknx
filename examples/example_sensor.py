import asyncio
from xknx import XKNX, Sensor

async def main():
    xknx = XKNX()
    await xknx.start()

    sensor1 = Sensor(
        xknx,
        'DiningRoom.Motion.Sensor',
        group_address='6/0/2',
        value_type='binary',
        device_class='motion')
    await sensor1.sync()
    print(sensor1)

    sensor2 = Sensor(
        xknx,
        'DiningRoom.Temperatur.Sensor',
        group_address='6/2/1',
        value_type='float',
        device_class='temperature')
    await sensor2.sync()
    print(sensor2)

    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
