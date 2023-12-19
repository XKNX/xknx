"""Example for writing an individual address to a KNX device."""
import asyncio

from xknx import XKNX
from xknx.management import procedures
from xknx.telegram import IndividualAddress


async def main():
    """
    Write the individual address 1.1.3 to a device in programming mode.

    This fails if multiple devices are in programming mode and/or when there is no device found in programming mode.
    """
    async with XKNX() as xknx:
        individual_address = IndividualAddress("1.1.3")
        task = asyncio.create_task(
            procedures.nm_invididual_address_write(xknx, individual_address)
        )
        await task


if __name__ == "__main__":
    asyncio.run(main())
