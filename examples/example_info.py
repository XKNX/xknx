"""Example on how to read mask version and properties from a KNX actor."""
import asyncio
import sys

from xknx import XKNX
from xknx.core import PayloadReader
from xknx.telegram import IndividualAddress
from xknx.telegram.apci import (
    DeviceDescriptorRead,
    DeviceDescriptorResponse,
    PropertyValueRead,
    PropertyValueResponse,
)


async def main(argv: list[str]):
    """Connect and read information from a KNX device. Requires a System B device."""
    if len(argv) == 2:
        address = IndividualAddress(argv[1])
    else:
        address = "1.1.1"

    xknx = XKNX()
    await xknx.start()

    reader = PayloadReader(xknx, address)

    # Read the mask version of the device (descriptor 0).
    payload = await reader.send(
        DeviceDescriptorRead(descriptor=0), response_class=DeviceDescriptorResponse
    )
    if payload is not None:
        print(f"Mask version: {payload.value:04x}")

    # Read the serial number of the device (object 0, property 11).
    payload = await reader.send(
        PropertyValueRead(object_index=0, property_id=11, count=1, start_index=1),
        response_class=PropertyValueResponse,
    )
    if payload is not None:
        print(
            f"Serial number: {payload.data[0]:02x}{payload.data[1]:02x}:"
            f"{payload.data[2]:02x}{payload.data[3]:02x}{payload.data[4]:02x}{payload.data[5]:02x}"
        )

    # Check if the device is in programming mode (object 0, property 54).
    payload = await reader.send(
        PropertyValueRead(object_index=0, property_id=54, count=1, start_index=1),
        response_class=PropertyValueResponse,
    )
    if payload is not None:
        print(f"Programming mode: {'ON' if payload.data[0] else 'OFF'}")

    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
