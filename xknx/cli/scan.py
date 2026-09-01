"""The `xknx scan` command."""

from __future__ import annotations

import argparse
import sys

from xknx import XKNX
from xknx.io import GatewayScanner

from ._command import Command


class ScanCommand(Command):
    """Scan for KNX/IP gateways."""

    name = "scan"
    help_text = "scan for KNX/IP gateways"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add the scan command arguments."""
        parser.add_argument(
            "--timeout",
            type=float,
            default=3.0,
            help="scan timeout in seconds (default: 3)",
        )

    async def run(self, args: argparse.Namespace) -> int:
        """Scan for KNX/IP gateways and print what is found."""
        if args.gateway is not None:
            print(
                "Error: --gateway is not applicable to 'scan' - it uses"
                " multicast discovery.",
                file=sys.stderr,
            )
            return 2
        gatewayscanner = GatewayScanner(
            XKNX(), local_ip=args.local_ip, timeout_in_seconds=args.timeout
        )
        async for gateway in gatewayscanner.async_scan():
            tunnelling = (
                "Secure"
                if gateway.tunnelling_requires_secure
                else "TCP"
                if gateway.supports_tunnelling_tcp
                else "UDP"
                if gateway.supports_tunnelling
                else "No"
            )
            routing = (
                "Secure"
                if gateway.routing_requires_secure
                else "Yes"
                if gateway.supports_routing
                else "No"
            )
            print(
                f"{gateway.individual_address} {gateway.ip_addr}:{gateway.port} "
                f"{gateway.name!r} tunnelling: {tunnelling} routing: {routing}"
            )
        if not gatewayscanner.found_gateways:
            print("No gateways found.")
        return 0
