"""Example on how to connect to restart a KNX device."""

import asyncio
import sys

from xknx import XKNX
from xknx.management.procedures import dm_restart
from xknx.telegram import IndividualAddress


async def main(argv: list[str]):
    """Restart a KNX device."""
    if len(argv) != 2:
        print(f"{argv[0]}: missing target address.")
        return 1

    address = IndividualAddress(argv[1])

    async with XKNX() as xknx:
        await dm_restart(xknx, address)


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
