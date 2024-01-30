"""Example for writing an individual address to a KNX device."""
import asyncio
import sys

from xknx import XKNX
from xknx.management import procedures
from xknx.telegram import IndividualAddress


async def main(argv: list[str]) -> int:
    """Write the individual address to a device."""

    if len(argv) != 3:
        print(
            f"{argv[0]}: required arguments: serial number formatted as f0:18:fa:23:d2:00 and individual address."
        )
        return 1

    serial = bytes.fromhex(argv[1].replace(":", ""))
    address = IndividualAddress(argv[2])

    print(f"Setting address {address} to device with serial {serial}")

    async with XKNX() as xknx:
        await procedures.nm_individual_address_serial_number_write(
            xknx, serial, address
        )

    return 0


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
