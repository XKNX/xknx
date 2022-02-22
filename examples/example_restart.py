"""Example on how to connect to restart a KNX device."""
import asyncio
import sys

from xknx import XKNX
from xknx.telegram import IndividualAddress, Telegram
from xknx.telegram.apci import Restart


async def main(argv: list[str]):
    """Restart a KNX device."""
    if len(argv) != 2:
        print(f"{argv[0]}: missing target address.")
        return 1

    address = IndividualAddress(argv[1])

    xknx = XKNX()
    await xknx.start()

    await xknx.telegrams.put(Telegram(address, payload=Restart()))
    await asyncio.sleep(2)

    await xknx.stop()


if __name__ == "__main__":
    asyncio.run(main(sys.argv))
