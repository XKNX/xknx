"""The `xknx group write` command."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTComplex, DPTString
from xknx.exceptions import ConversionError
from xknx.telegram import Telegram
from xknx.telegram.apci import GroupValueWrite

from .._command import dpt_argument, group_address_argument
from ._base import GroupCommand


def parse_typed_value(raw: str, transcoder: type[DPTBase]) -> Any:
    """Parse a command line value for a DPT transcoder."""
    if issubclass(transcoder, DPTComplex):
        # structured DPTs take a JSON object, e.g. '{"red": 255, ...}'
        try:
            return json.loads(raw)
        except json.JSONDecodeError as err:
            raise ConversionError(f"invalid JSON value: {err}") from None
    if issubclass(transcoder, DPTString):
        # literal text - don't interpret 'true', 'null' or '1e2'
        return raw
    try:
        return json.loads(raw)  # numbers and booleans, e.g. '21.5' or 'true'
    except json.JSONDecodeError:
        return raw  # plain strings, e.g. 'on' or 'comfort'


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


def parse_raw_payload(raw: str) -> DPTBinary | DPTArray | None:
    """Parse an untyped payload: 'on'/'off', an integer 0-63 or a hex byte string."""
    value = parse_raw_value(raw)
    if isinstance(value, int) and 0 <= value <= 63:
        return DPTBinary(value)
    if isinstance(value, str) and value:
        try:
            return DPTArray(tuple(bytes.fromhex(value)))
        except ValueError:
            return None
    return None


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
            help="value to write: 'on'/'off', a raw integer 0-63 or a hex byte"
            " string without --type, otherwise a value for the given DPT,"
            " e.g. '21.5' with --type 9.001 or a JSON object for structured DPTs",
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
            try:
                args.value = args.type.to_knx(parse_typed_value(args.value, args.type))
            except ConversionError as err:
                print(f"Error: {err.description}", file=sys.stderr)
                return 2
        else:
            payload = parse_raw_payload(args.value)
            if payload is None:
                print(
                    "Error: --type is required for values other than 'on'/'off',"
                    " raw integers 0-63 or hex byte strings.",
                    file=sys.stderr,
                )
                return 2
            args.value = payload
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
