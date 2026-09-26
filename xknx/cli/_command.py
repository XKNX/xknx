"""Base class and shared helpers for xknx CLI commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
from typing import ClassVar

from xknx.io import DEFAULT_MCAST_PORT, ConnectionConfig, ConnectionType


def gateway_argument(value: str) -> tuple[str, int]:
    """Parse and validate a gateway 'host[:port]' command line argument."""
    host, _, port_str = value.partition(":")
    if "[" in value or ":" in port_str:
        # the KNX/IP interface resolves IPv4 addresses only
        raise argparse.ArgumentTypeError("IPv6 gateway addresses are not supported")
    if any(char in value for char in "/@?#"):
        raise argparse.ArgumentTypeError(f"expected 'host[:port]', got {value!r}")
    if not host:
        raise argparse.ArgumentTypeError(f"missing host in {value!r}")
    port = DEFAULT_MCAST_PORT
    if port_str:
        try:
            port = int(port_str)
        except ValueError:
            raise argparse.ArgumentTypeError(f"invalid port {port_str!r}") from None
        if not 1 <= port <= 65535:
            raise argparse.ArgumentTypeError(f"port out of range: {port}")
    return host, port


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
