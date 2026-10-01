"""The `xknx group monitor` command."""

from __future__ import annotations

import argparse
import asyncio

from xknx import XKNX
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

from .._command import address_filter_argument, format_value
from ._base import GroupCommand


async def _block_forever() -> None:
    """Wait until the running task is cancelled."""
    await asyncio.Event().wait()


def print_telegram(telegram: Telegram) -> None:
    """Print a received telegram."""
    if isinstance(telegram.payload, GroupValueWrite | GroupValueResponse):
        payload = format_value(telegram.payload.value.value)
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
        super().configure(parser)
        parser.add_argument(
            "--filter",
            action="append",
            type=address_filter_argument,
            help="group address pattern, e.g. '1/2/*' or '1/4/5-6,8';"
            " repeat the option for multiple filters",
        )

    async def run_connected(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Print telegrams from the KNX bus until interrupted."""
        xknx.telegram_queue.register_telegram_received_cb(print_telegram, args.filter)
        # Ctrl+C ends the command with exit code 130: asyncio.run() cancels
        # this task so the connection is torn down cleanly, and a second
        # Ctrl+C - e.g. during a disconnect to a gone gateway - aborts that.
        await _block_forever()
        return 0
