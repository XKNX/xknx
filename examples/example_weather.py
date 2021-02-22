"""Example for Weather device. See docs/weather.md for a detailed explanation."""
import asyncio
import logging

from xknx import XKNX
from xknx.devices import Weather

logging.basicConfig(level=logging.WARN)


async def main():
    """Connect to KNX/IP device and create a weather device and read its sensors."""
    xknx = XKNX()
    await xknx.start()

    weather = Weather(
        xknx,
        "Home",
        group_address_temperature="7/0/1",
        group_address_brightness_south="7/0/5",
        group_address_brightness_east="7/0/4",
        group_address_brightness_west="7/0/3",
        group_address_wind_speed="7/0/2",
        group_address_wind_bearing="7/0/6",
        group_address_day_night="7/0/7",
        group_address_rain_alarm="7/0/0",
    )

    await weather.sync(wait_for_result=True)
    print(weather.max_brightness)
    print(weather.ha_current_state())
    print(weather)

    await xknx.stop()


asyncio.run(main())
