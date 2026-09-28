"""The `xknx group write` command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.exceptions import ConversionError
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueWrite

from .._command import dpt_argument, group_address_argument
from ._base import GroupCommand


def parse_raw_value(raw: str) -> bool | int | float | str:
    """Parse a raw command line value into a Python value."""
    if raw.lower() in ("on", "true"):
        return True
    if raw.lower() in ("off", "false"):
        return False
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


class WriteCommand(GroupCommand):
    """Write a value to a group address."""

    name = "write"
    help_text = "write a value to a group address"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add the write command arguments."""
        super().configure(parser)
        parser.add_argument(
            "group_address",
            type=group_address_argument,
            help="KNX group address, e.g. '1/2/3'",
        )
        parser.add_argument(
            "value",
            help="value to write: 'on'/'off' or a raw integer 0-63 without --type,"
            " otherwise a value for the given DPT, e.g. '21.5' with --type 9.001"
            " or a JSON object for structured DPTs",
        )
        parser.add_argument(
            "--type",
            type=dpt_argument,
            help="DPT value type, e.g. 'percent' or '9.001'",
        )

    async def run(self, args: argparse.Namespace) -> int:
        """Validate the value before connecting."""
        if args.type is not None:
            # convert before connecting to fail early for invalid values -
            # the encoded payload is passed through to `run_connected`
            value: Any = args.value
            if value.startswith("{"):
                # structured DPTs take a JSON object, e.g. '{"red": 255, ...}'
                try:
                    value = json.loads(value)
                except json.JSONDecodeError as err:
                    raise ConversionError(f"invalid JSON value: {err}") from None
            try:
                args.value = args.type.to_knx(value)
            except ConversionError:
                # retry with a parsed bool/int/float - e.g. 'true' for DPT 1.x
                fallback = parse_raw_value(value) if isinstance(value, str) else value
                if isinstance(fallback, str) or fallback is value:
                    raise
                args.value = args.type.to_knx(fallback)
        else:
            value = parse_raw_value(args.value)
            if not isinstance(value, int) or not 0 <= value <= 63:
                print(
                    "Error: --type is required for values other than 'on'/'off' "
                    "or raw integers 0-63.",
                    file=sys.stderr,
                )
                return 1
            args.value = DPTBinary(value)
        return await super().run(args)

    async def run_connected(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Send a GroupValueWrite telegram and wait for its confirmation."""
        await xknx.cemi_handler.send_telegram(
            Telegram(
                destination_address=args.group_address,
                payload=GroupValueWrite(args.value),
            )
        )
        return 0
