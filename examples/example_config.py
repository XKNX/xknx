"""Example for config file parser."""
import asyncio

from xknx import XKNX


async def main():
    """Read xknx.yaml, walk through all devices and print them."""
    xknx = XKNX()

    for device in xknx.devices:
        print(device)


asyncio.run(main())
