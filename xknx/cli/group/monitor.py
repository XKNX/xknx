"""The `xknx group monitor` command."""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import signal

from xknx import XKNX
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

from .._command import address_filter_argument
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
        await self._wait_for_sigint()
        return 0

    @staticmethod
    async def _wait_for_sigint() -> None:
        """Block until the first Ctrl+C, leaving teardown interruptible."""
        sigint_received = asyncio.Event()
        loop = asyncio.get_running_loop()
        with contextlib.suppress(NotImplementedError):  # signals need Unix
            # Windows: Ctrl+C raises KeyboardInterrupt through asyncio instead
            loop.add_signal_handler(signal.SIGINT, sigint_received.set)
        try:
            await sigint_received.wait()
        finally:
            # a second Ctrl+C - e.g. during a hanging disconnect - uses the
            # default handler again and raises KeyboardInterrupt
            with contextlib.suppress(NotImplementedError):
                loop.remove_signal_handler(signal.SIGINT)
