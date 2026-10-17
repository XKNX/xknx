"""Command line interface for xknx."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Coroutine, Sequence
import logging
import sys
from typing import Any

from xknx.exceptions import ConversionError, XKNXException

from . import group, scan
from ._command import Command
from .group import GroupCommand
from .scan import ScanCommand

__all__ = ["group", "main", "scan"]


def _add_command(subparsers: Any, command_cls: type[Command]) -> None:
    """Register a command class with a subparsers action."""
    command = command_cls()
    subparser = subparsers.add_parser(command.name, help=command.help_text)
    command.configure(subparser)
    subparser.set_defaults(func=command.run)


def _add_command_group(
    subparsers: Any,
    group_cls: type[Command],
    command_classes: Sequence[type[Command]],
) -> None:
    """Register a command group and its commands with a subparsers action."""
    group_parser = subparsers.add_parser(group_cls.name, help=group_cls.help_text)
    group_subparsers = group_parser.add_subparsers(
        title="commands",
        metavar="<command>",
        dest="subcommand",
        required=True,
        help=f"run 'xknx {group_cls.name} <command> --help'"
        " for command specific options",
    )
    for command_cls in command_classes:
        _add_command(group_subparsers, command_cls)


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
    subparsers = parser.add_subparsers(
        title="commands",
        metavar="<command>",
        dest="command",
        required=True,
        help="run 'xknx <command> --help' for command specific options",
    )

    _add_command_group(
        subparsers,
        GroupCommand,  # type: ignore[type-abstract]  # only name/help_text are read
        group.COMMANDS,
    )
    _add_command(subparsers, ScanCommand)

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
    except ConversionError as err:
        print(f"Error: {err.description}", file=sys.stderr)
        return 1
    except (XKNXException, OSError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
