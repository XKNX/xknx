"""Example for sending generic telegrams to the KNX bus."""
import asyncio
import logging

from xknx import XKNX
from xknx.tools import group_value_response, group_value_write

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.tools").level = logging.DEBUG


async def main() -> None:
    """Connect to KNX bus and send telegrams."""
    async with XKNX() as xknx:
        # send a DPT 9.001 temperature value
        await group_value_write(xknx, "5/1/20", 21.7, value_type="temperature")
        # send a response DPT 1 binary value
        await group_value_response(xknx, "5/1/20", True)


asyncio.run(main())
