"""Base class and shared helpers for xknx CLI commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
import ipaddress
import json
import os
from typing import Any, ClassVar

from xknx.dpt import DPTBase, DPTComplexData, DPTEnumData
from xknx.exceptions import ConversionError, CouldNotParseAddress
from xknx.io import DEFAULT_MCAST_PORT, ConnectionConfig, ConnectionType
from xknx.telegram import AddressFilter, GroupAddress


def format_value(value: Any) -> str:
    """Format a value so it can be passed back to `group write`."""
    if isinstance(value, DPTComplexData):
        return json.dumps(value.as_dict())
    if isinstance(value, DPTEnumData):
        return value.name.lower()
    if isinstance(value, tuple):  # raw payload read without a DPT
        # the prefix tells it apart from a 6-bit integer, e.g. 0x21 vs 21
        return f"0x{bytes(value).hex()}"
    return str(value)


def group_address_argument(value: str) -> GroupAddress:
    """Parse a group address command line argument."""
    try:
        return GroupAddress(value)
    except CouldNotParseAddress as err:
        raise argparse.ArgumentTypeError(
            f"invalid group address {value!r}: {err.message}"
        ) from None


def dpt_argument(value: str) -> type[DPTBase]:
    """Parse a DPT value type command line argument."""
    try:
        return DPTBase.get_dpt(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"unknown DPT value type {value!r}") from None


def address_filter_argument(value: str) -> AddressFilter:
    """Parse an address filter pattern command line argument."""
    try:
        return AddressFilter(value)
    except (ConversionError, CouldNotParseAddress, ValueError):
        raise argparse.ArgumentTypeError(
            f"invalid address filter pattern {value!r}"
        ) from None


def _is_ipv6_address(value: str) -> bool:
    """Return if value is an IPv6 address, optionally as '[address]:port'."""
    host = value[1 : value.find("]")] if value.startswith("[") else value
    try:
        ipaddress.IPv6Address(host)
    except ValueError:
        return False
    return True


def gateway_argument(value: str) -> tuple[str, int]:
    """Parse and validate a gateway 'host[:port]' command line argument."""
    if value.startswith("[") or value.count(":") > 1:
        if _is_ipv6_address(value):
            # the KNX/IP interface resolves IPv4 addresses only
            raise argparse.ArgumentTypeError("IPv6 gateway addresses are not supported")
        raise argparse.ArgumentTypeError(f"expected 'host[:port]', got {value!r}")
    if any(char in value for char in "/@?#"):
        raise argparse.ArgumentTypeError(f"expected 'host[:port]', got {value!r}")
    host, separator, port_str = value.partition(":")
    if not host:
        raise argparse.ArgumentTypeError(f"missing host in {value!r}")
    if separator and not port_str:
        raise argparse.ArgumentTypeError(f"missing port in {value!r}")
    port = DEFAULT_MCAST_PORT
    if port_str:
        try:
            port = int(port_str)
        except ValueError:
            raise argparse.ArgumentTypeError(f"invalid port {port_str!r}") from None
        if not 1 <= port <= 65535:
            raise argparse.ArgumentTypeError(f"port out of range: {port}")
    return host, port


def add_gateway_argument(parser: argparse.ArgumentParser) -> None:
    """Add the --gateway option to a command parser."""
    parser.add_argument(
        "--gateway",
        type=gateway_argument,
        default=os.environ.get("XKNX_GATEWAY"),
        help="KNX/IP gateway as 'host[:port]' for UDP tunneling"
        " (default: XKNX_GATEWAY environment variable, or automatic discovery)",
    )


def add_local_ip_argument(parser: argparse.ArgumentParser) -> None:
    """Add the --local-ip option to a command parser."""
    parser.add_argument(
        "--local-ip",
        default=os.environ.get("XKNX_LOCAL_IP"),
        help="local IP address or interface name to use"
        " (default: XKNX_LOCAL_IP environment variable)",
    )


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

    Commands are registered explicitly: top level commands and command
    groups in `xknx.cli._parser()`, the commands of a group in the
    `COMMANDS` tuple of the group's package (see `xknx.cli.group`).
    """

    name: ClassVar[str]
    help_text: ClassVar[str]

    def configure(self, parser: argparse.ArgumentParser) -> None:  # noqa: B027
        """Add command specific arguments to the parser - optional override."""

    @abstractmethod
    async def run(self, args: argparse.Namespace) -> int:
        """Run the command."""
