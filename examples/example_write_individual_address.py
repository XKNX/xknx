"""Example for writing an individual address to a KNX device."""

import asyncio
import sys

from xknx import XKNX
from xknx.management import procedures
from xknx.telegram import IndividualAddress


async def main(argv: list[str]) -> int:
    """
    Write the individual address to a device in programming mode.

    This fails if multiple devices are in programming mode and/or when there is no device found in programming mode.
    """

    if len(argv) != 2:
        print(f"{argv[0]}: missing target address.")
        return 1

    address = IndividualAddress(argv[1])

    async with XKNX() as xknx:
        individual_address = IndividualAddress(address)
        await procedures.nm_individual_address_write(xknx, individual_address)

    return 0


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
