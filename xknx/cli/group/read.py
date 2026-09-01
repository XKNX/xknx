"""The `xknx group read` command."""

from __future__ import annotations

import argparse
import sys

from xknx import XKNX
from xknx.dpt import DPTBase
from xknx.telegram import GroupAddress
from xknx.tools import read_group_value

from ._base import GroupCommand


class ReadCommand(GroupCommand):
    """Read the value of a group address."""

    name = "read"
    help_text = "read a group address value"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add the read command arguments."""
        parser.add_argument("group_address", help="KNX group address, e.g. '1/2/3'")
        parser.add_argument(
            "--type", help="DPT value type, e.g. 'temperature' or '9.001'"
        )

    async def run(self, args: argparse.Namespace) -> int:
        """Validate the group address and value type before connecting."""
        # parsed results are passed through to `run_connected`
        args.group_address = GroupAddress(args.group_address)
        if args.type is not None:
            args.type = DPTBase.get_dpt(args.type)  # raises ValueError if unknown
        return await super().run(args)

    async def run_connected(self, xknx: XKNX, args: argparse.Namespace) -> int:
        """Read the value of a group address and print it."""
        value = await read_group_value(xknx, args.group_address, value_type=args.type)
        if value is None:
            print("No response received.", file=sys.stderr)
            return 1
        print(value)
        return 0
