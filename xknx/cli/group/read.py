"""The `xknx group read` command."""

from __future__ import annotations

import argparse
import sys

from xknx import XKNX
from xknx.tools import read_group_value

from .._command import dpt_argument, format_value, group_address_argument
from ._base import GroupCommand


class ReadCommand(GroupCommand):
    """Read the value of a group address."""

    name = "read"
    help_text = "read a group address value"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add the read command arguments."""
        super().configure(parser)
        parser.add_argument(
            "group_address",
            type=group_address_argument,
            help="KNX group address, e.g. '1/2/3'",
        )
        parser.add_argument(
            "--type",
            type=dpt_argument,
            help="DPT value type, e.g. 'temperature' or '9.001'",
        )

    async def run_connected(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Read the value of a group address and print it."""
        value = await read_group_value(xknx, args.group_address, value_type=args.type)
        if value is None:
            print("No response received.", file=sys.stderr)
            return 1
        print(format_value(value))
        return 0
