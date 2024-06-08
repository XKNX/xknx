"""Example for Sensor device. See docs/sensor.md and docs/binary_sensor.md for a detailed explanation."""

import asyncio

from xknx import XKNX
from xknx.devices import BinarySensor, Sensor


async def main() -> None:
    """Connect to KNX/IP device and read the value of a temperature and a motion sensor."""
    xknx = XKNX()
    await xknx.start()

    sensor1 = BinarySensor(
        xknx,
        "DiningRoom.Motion.Sensor",
        group_address_state="6/0/2",
    )
    xknx.devices.async_add(sensor1)
    await sensor1.sync(wait_for_result=True)
    print(sensor1)

    sensor2 = Sensor(
        xknx,
        "DiningRoom.Temperature.Sensor",
        group_address_state="6/2/1",
        value_type="temperature",
    )
    xknx.devices.async_add(sensor2)

    await sensor2.sync(wait_for_result=True)
    print(sensor2)

    await xknx.stop()


asyncio.run(main())
