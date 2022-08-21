"""Example for the telegram monitor callback."""
import argparse
import asyncio
import logging
import textwrap

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, DPTTemperature
from xknx.io.connection import ConnectionConfigUSB
from xknx.telegram import AddressFilter, Telegram


logger = logging.getLogger("xknx.log")
logger.setLevel(logging.DEBUG)


async def telegram_received_cb(telegram: Telegram):
    """Do something with the received telegram."""
    logger.debug(f"Telegram received: {telegram}")


async def monitor(address_filters):
    """Set telegram_received_cb within XKNX and connect to USB device in daemon mode."""
    xknx = XKNX(connection_config=ConnectionConfigUSB(), daemon_mode=True)
    xknx.telegram_queue.register_telegram_received_cb(
        telegram_received_cb, address_filters
    )
    await xknx.start()
    await xknx.stop()


async def main(args):
    address_filters = None
    if args.filter:
        address_filters = list(map(AddressFilter, args.filter))
    await monitor(address_filters)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="",
        epilog=textwrap.dedent(
            r"""
            Listen to all telegrams

            Examples
            --------
            Monitor all events on address 0/0/*
                > python examples/usb/example_telegram_monitor.py --filter "0/0/*"
            """
        ),
    )
    parser.add_argument(
        "-f",
        "--filter",
        help="Filter for specific group addresses (1/2/*,1/4/[5-6])",
        type=str,
        default=None,
        required=True,
    )
    parser.add_argument("-v", "--version", action="version", version="0.1")
    args = parser.parse_args()
    asyncio.run(main(args))
