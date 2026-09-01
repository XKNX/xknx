"""Command line interface for xknx."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Coroutine, Sequence
import logging
import sys
from typing import Any

from xknx.exceptions import XKNXException

from . import group, scan
from ._command import Command, gateway_argument

__all__ = ["group", "main", "scan"]


def _add_command(subparsers: Any, command_cls: type[Command]) -> None:
    """Register a command class with a subparsers action."""
    command = command_cls()
    subparser = subparsers.add_parser(command.name, help=command.help_text)
    command.configure(subparser)
    subparser.set_defaults(func=command.run)


def _parser() -> argparse.ArgumentParser:
    """Create the xknx argument parser."""
    parser = argparse.ArgumentParser(
        prog="xknx", description="Command line interface for xknx."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="increase verbosity (-v: info, -vv: debug)",
    )
    parser.add_argument(
        "--gateway",
        type=gateway_argument,
        help="KNX/IP tunneling gateway as 'host[:port]' (default: automatic discovery)",
    )
    parser.add_argument("--local-ip", help="local IP address or interface name to use")
    subparsers = parser.add_subparsers(
        title="commands",
        metavar="<command>",
        dest="command",
        required=True,
        help="run 'xknx <command> --help' for command specific options",
    )

    for command_cls in Command.subcommands():
        if subcommand_classes := command_cls.subcommands():
            group_parser = subparsers.add_parser(
                command_cls.name, help=command_cls.help_text
            )
            group_subparsers = group_parser.add_subparsers(
                title="commands",
                metavar="<command>",
                dest="subcommand",
                required=True,
                help=f"run 'xknx {command_cls.name} <command> --help'"
                " for command specific options",
            )
            for subcommand_cls in subcommand_classes:
                _add_command(group_subparsers, subcommand_cls)
        else:
            _add_command(subparsers, command_cls)

    return parser


def _setup_logging(verbosity: int) -> None:
    """Configure logging according to the verbosity level."""
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity > 1:
        level = logging.DEBUG
    logging.basicConfig(level=level)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the xknx command line interface."""
    args = _parser().parse_args(argv)
    _setup_logging(args.verbose)
    handler: Callable[[argparse.Namespace], Coroutine[Any, Any, int]] = args.func
    try:
        return asyncio.run(handler(args))
    except KeyboardInterrupt:
        return 130  # 128 + SIGINT
    except (XKNXException, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
