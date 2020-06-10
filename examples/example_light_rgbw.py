"""Example for setting different colors on a RGBW remote value."""
import anyio

from xknx import XKNX
from xknx.remote_value import RemoteValueColorRGBW


async def main():
    """Connect to KNX/IP bus and set different colors."""
    async with XKNX().run() as xknx:

        rgbw = RemoteValueColorRGBW(xknx,
                                    group_address='1/1/40',
                                    group_address_state='1/1/41',
                                    device_name="RGBWLight")

        await rgbw.set([255, 255, 255, 0, 15])  # cold-white
        await anyio.sleep(1)
        await rgbw.set([0, 0, 0, 255, 15])  # warm-white
        await anyio.sleep(1)
        await rgbw.set([0, 0, 0, 0, 15])  # off
        await anyio.sleep(1)

        await rgbw.set([255, 0, 0, 0])  # red
        await anyio.sleep(1)
        await rgbw.set([0, 255, 0, 0])  # green
        await anyio.sleep(1)
        await rgbw.set([0, 0, 255, 0])  # blue
        await anyio.sleep(1)
        await rgbw.set([0, 0, 0, 0, 15])  # off
        await anyio.sleep(1)

        await rgbw.set([255, 255, 0, 0, 15])
        await anyio.sleep(1)
        await rgbw.set([0, 255, 255, 0, 15])
        await anyio.sleep(1)
        await rgbw.set([255, 0, 255, 0, 15])
        await anyio.sleep(1)
        await rgbw.set([0, 0, 0, 0, 15])  # off
        await anyio.sleep(1)


anyio.run(main)
