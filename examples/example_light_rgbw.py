"""Example for setting different colors on a RGBW remote value."""

import asyncio

from xknx import XKNX
from xknx.dpt.dpt_color import RGBWColor
from xknx.remote_value import RemoteValueColorRGBW


async def main() -> None:
    """Connect to KNX/IP bus and set different colors."""
    xknx = XKNX()
    await xknx.start()

    rgbw = RemoteValueColorRGBW(
        xknx,
        group_address="1/1/40",
        group_address_state="1/1/41",
        device_name="RGBWLight",
    )

    await rgbw.set(RGBWColor(255, 255, 255, 0))  # cold-white
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 0, 0, 255))  # warm-white
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 0, 0, 0))  # off
    await asyncio.sleep(1)

    await rgbw.set(RGBWColor(255, 0, 0, 0))  # red
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 255, 0, 0))  # green
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 0, 255, 0))  # blue
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 0, 0, 0))  # off
    await asyncio.sleep(1)

    await rgbw.set(RGBWColor(255, 255, 0, 0))
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 255, 255, 0))
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(255, 0, 255, 0))
    await asyncio.sleep(1)
    await rgbw.set(RGBWColor(0, 0, 0, 0))  # off
    await asyncio.sleep(1)

    await xknx.stop()


asyncio.run(main())
