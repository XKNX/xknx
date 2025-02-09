"""Example for the telegram monitor callback."""

import asyncio
import getopt  # pylint: disable=deprecated-module
import sys

from xknx import XKNX
from xknx.telegram import AddressFilter, Telegram


def telegram_received_cb(telegram: Telegram) -> None:
    """Do something with the received telegram."""
    print(f"Telegram received: {telegram}")


def show_help() -> None:
    """Print Help."""
    print("Telegram filter.")
    print()
    print("Usage:")
    print()
    print(__file__, "                            Listen to all telegrams")
    print(
        __file__, "-f --filter 1/2/*,1/4/[5-6]    Filter for specific group addresses"
    )
    print(__file__, "-h --help                      Print help")
    print()


async def monitor(address_filters: list[AddressFilter] | None) -> None:
    """Set telegram_received_cb within XKNX and connect to KNX/IP device in daemon mode."""
    xknx = XKNX(daemon_mode=True)
    xknx.telegram_queue.register_telegram_received_cb(
        telegram_received_cb, address_filters
    )
    await xknx.start()
    await xknx.stop()


async def main(argv: list[str]) -> None:
    """Parse command line arguments and start monitor."""
    try:
        opts, _ = getopt.getopt(argv, "hf:", ["help", "filter="])
    except getopt.GetoptError:
        show_help()
        sys.exit(2)
    address_filters = None
    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            show_help()
            sys.exit()
        if opt in ["-f", "--filter"]:
            address_filters = list(map(AddressFilter, arg.split(",")))
    await monitor(address_filters)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
