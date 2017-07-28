"""Example for config file parser."""
import asyncio
from xknx import XKNX

async def main():
    """Read xknx.yaml, walk through all devices and print them."""
    xknx = XKNX(config='xknx.yaml')

    for device in xknx.devices:
        print(device)

# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
