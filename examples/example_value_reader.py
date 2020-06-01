"""Example on how to read a value from KNX bus."""
import asyncio

from xknx import XKNX
from xknx.core import ValueReader
from xknx.telegram import GroupAddress


async def main():
    """Connect and read value from KNX bus."""
    async with XKNX().run() as xknx:

        value_reader = ValueReader(xknx, GroupAddress('2/0/8'))
        telegram = await value_reader.read()
        if telegram is not None:
            print(telegram)

        value_reader = ValueReader(xknx, GroupAddress('2/1/8'))
        telegram = await value_reader.read()
        if telegram is not None:
            print(telegram)


# pylint: disable=invalid-name
asyncio.run(main())
