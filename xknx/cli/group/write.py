"""The `xknx group write` command."""

from __future__ import annotations

import argparse
import sys

from xknx import XKNX
from xknx.dpt import DPTBase
from xknx.tools import group_value_write

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
        parser.add_argument("group_address", help="KNX group address, e.g. '1/2/3'")
        parser.add_argument("value", help="value to write, e.g. 'on', '50' or '21.5'")
        parser.add_argument("--type", help="DPT value type, e.g. 'percent' or '9.001'")

    async def run(self, args: argparse.Namespace) -> int:
        """Validate the value and value type before connecting."""
        if args.type is not None:
            # the raw string value is parsed by the DPT transcoder in `execute`
            DPTBase.get_dpt(args.type)  # raises ValueError for unknown types
        else:
            value = parse_raw_value(args.value)
            if not isinstance(value, int) or not 0 <= value <= 63:
                print(
                    "Error: --type is required for values other than 'on'/'off' "
                    "or raw integers 0-63.",
                    file=sys.stderr,
                )
                return 1
            args.value = value
        return await super().run(args)

    async def execute(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Send a GroupValueWrite telegram."""
        group_value_write(xknx, args.group_address, args.value, value_type=args.type)
        return 0
