"""Example for reading the serial number of a KNX device."""

import asyncio
import sys

from xknx import XKNX
from xknx.management import procedures
from xknx.profile import ResourceGenericPropertyId
from xknx.telegram import IndividualAddress, apci


async def read_serial_number(
    xknx: XKNX, individual_address: IndividualAddress
) -> bytes | None:
    """Read the serial number of a KNX device."""
    async with xknx.management.connection(address=individual_address) as connection:
        response = await connection.request(
            payload=apci.PropertyValueRead(
                property_id=ResourceGenericPropertyId.PID_SERIAL_NUMBER
            ),
            expected=apci.PropertyValueResponse,
        )
    if response.payload is None:
        print(f"Reading serial number from {individual_address} failed.")
        return None

    assert isinstance(response.payload, apci.PropertyValueResponse)
    return response.payload.data


async def main(argv: list[str]) -> int:
    """
    Read serial number from a device by given individual address or in programming mode.

    When no individual address is given, a device in programming mode is searched for.
    This fails if multiple devices are in programming mode and/or when there is no device found in programming mode.
    """
    individual_address: IndividualAddress | None = None

    if len(argv) == 2:
        individual_address = IndividualAddress(argv[1])
        print(
            f"Using individual address {individual_address} from command line argument."
        )

    async with XKNX() as xknx:
        if not individual_address:
            print("Searching for device in programming mode...")
            found = await procedures.nm_individual_address_read(
                xknx, raise_if_multiple=True
            )
            if not found:
                print("No device in programming mode found.")
                return 1
            individual_address = found[0]
            print(
                f"Found device in programming mode with individual address {individual_address}."
            )

        serial_number = await read_serial_number(xknx, individual_address)
        if serial_number is None:
            print("Failed to read serial number.")
            return 1
        # format the serial number in same style as ETS
        serial_string = f"{serial_number[:2].hex()}:{serial_number[2:].hex()}"
        print(f"Serial number of {individual_address} is {serial_string}.")

    return 0


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
