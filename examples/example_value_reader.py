"""Example on how to read a value from KNX bus."""
import asyncio

from xknx import XKNX
from xknx.core import ValueReader
from xknx.knx import GroupAddress


async def main():
    """Connect and read value from KNX bus."""
    xknx = XKNX()
    await xknx.start()

    value_reader = ValueReader(xknx, GroupAddress('6/2/1'))
    telegram = await value_reader.read()
    if telegram is not None:
        print(telegram)

    await xknx.stop()


# pylint: disable=invalid-name
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
