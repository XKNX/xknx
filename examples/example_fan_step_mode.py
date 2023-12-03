"""Example for Fan device."""
import asyncio

from xknx import XKNX
from xknx.devices import Fan


async def main():
    """Connect to KNX/IP bus, control a fan, and turn it off afterwards."""
    xknx = XKNX()
    await xknx.start()

    fan = Fan(
        xknx,
        name="TestFan",
        group_address_switch="1/0/12",
        group_address_speed="1/0/14",
        max_step=3,
    )

    # Turn on the fan
    await fan.turn_on()

    # Set fan speed in steps
    for step in range(1, fan.max_step + 1):
        await fan.set_speed(step)
        await asyncio.sleep(1)

    # Turn off the fan
    await fan.turn_off()

    await xknx.stop()


asyncio.run(main())
