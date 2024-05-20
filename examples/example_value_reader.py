"""Example on how to read a value from KNX bus."""

import asyncio

from xknx import XKNX
from xknx.core import ValueReader
from xknx.telegram import GroupAddress
from xknx.tools import read_group_value


async def main() -> None:
    """Connect and read value from KNX bus."""
    async with XKNX() as xknx:
        # get the value only (can be decoded when passing `value_type`)
        result = await read_group_value(xknx, "5/1/20")
        print(f"Value: {result}")

        # get the whole telegram
        telegram = await ValueReader(xknx, GroupAddress("5/1/20")).read()
        print(f"Telegram: {telegram}")


asyncio.run(main())
