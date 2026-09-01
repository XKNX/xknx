"""Base class and shared helpers for xknx CLI commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
from typing import ClassVar
from urllib.parse import urlsplit

from xknx.io import DEFAULT_MCAST_PORT, ConnectionConfig, ConnectionType


def gateway_argument(value: str) -> tuple[str, int]:
    """Parse and validate a gateway 'host[:port]' command line argument."""
    try:
        split = urlsplit(f"//{value}")
        host = split.hostname
        port = split.port  # raises ValueError for invalid or out of range ports
    except ValueError as err:
        raise argparse.ArgumentTypeError(str(err)) from None
    if not host:
        raise argparse.ArgumentTypeError(f"missing host in {value!r}")
    if port == 0:
        raise argparse.ArgumentTypeError("port out of range: 0")
    return host, port if port is not None else DEFAULT_MCAST_PORT


def connection_config(args: argparse.Namespace) -> ConnectionConfig:
    """Build a ConnectionConfig from the global command line options."""
    if args.gateway is not None:
        host, port = args.gateway
        return ConnectionConfig(
            connection_type=ConnectionType.TUNNELING,
            gateway_ip=host,
            gateway_port=port,
            local_ip=args.local_ip,
        )
    return ConnectionConfig(local_ip=args.local_ip)


class Command(ABC):
    """
    Base class for xknx CLI commands.

    Direct subclasses form the top level of the command line interface.
    A concrete subclass is a command; an abstract subclass with subclasses
    of its own is a command group whose members are its direct subclasses
    (see `xknx.cli.group`).
    """

    name: ClassVar[str]
    help_text: ClassVar[str]

    @classmethod
    def subcommands(cls) -> list[type[Command]]:
        """Return the directly derived command classes."""
        return cls.__subclasses__()

    def configure(self, parser: argparse.ArgumentParser) -> None:  # noqa: B027
        """Add command specific arguments to the parser - optional override."""

    @abstractmethod
    async def run(self, args: argparse.Namespace) -> int:
        """Run the command."""
