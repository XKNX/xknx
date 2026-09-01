"""The `xknx group monitor` command."""

from __future__ import annotations

import argparse

from xknx import XKNX
from xknx.telegram import AddressFilter, Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

from ._base import GroupCommand


def print_telegram(telegram: Telegram) -> None:
    """Print a received telegram."""
    payload: str | int | tuple[int, ...]
    if isinstance(telegram.payload, GroupValueWrite | GroupValueResponse):
        payload = telegram.payload.value.value
    else:
        payload = telegram.payload.__class__.__name__
    print(
        f"{telegram.direction.value:8} {telegram.source_address!s:20} | "
        f"{telegram.destination_address!s:24} | {payload}"
    )


class MonitorCommand(GroupCommand):
    """Print group telegrams from the KNX bus."""

    name = "monitor"
    help_text = "print group telegrams from the KNX bus"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add the monitor command arguments."""
        parser.add_argument(
            "--filter",
            help="comma-separated group address patterns, e.g. '1/2/*,1/4/5-6'",
        )

    async def execute(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Print telegrams from the KNX bus until interrupted."""
        address_filters = (
            [AddressFilter(pattern) for pattern in args.filter.split(",")]
            if args.filter
            else None
        )
        xknx.telegram_queue.register_telegram_received_cb(
            print_telegram, address_filters
        )
        await xknx.loop_until_sigint()
        return 0
