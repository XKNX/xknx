"""The `xknx scan` command."""

from __future__ import annotations

import argparse
import asyncio
import ipaddress
import logging
import sys

from xknx import XKNX
from xknx.exceptions import XKNXException
from xknx.io import GatewayDescriptor, GatewayScanner
from xknx.io.util import get_local_ips

from ._command import Command, add_local_ip_argument

logger = logging.getLogger("xknx.cli")


def _print_gateway(gateway: GatewayDescriptor) -> None:
    """Print a found gateway."""
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


class ScanCommand(Command):
    """Scan for KNX/IP gateways."""

    name = "scan"
    help_text = "scan for KNX/IP gateways"

    def configure(self, parser: argparse.ArgumentParser) -> None:
        """Add the scan command arguments."""
        add_local_ip_argument(parser)
        parser.add_argument(
            "--timeout",
            type=float,
            default=3.0,
            help="scan timeout in seconds (default: 3)",
        )

    async def run(self, args: argparse.Namespace) -> int:
        """Scan for KNX/IP gateways on all interfaces and print what is found."""
        if args.local_ip is not None:
            local_ips = [args.local_ip]
        else:
            local_ips = [
                ip.ip
                for ip in get_local_ips()
                if isinstance(ip.ip, str)
                and not ipaddress.IPv4Address(ip.ip).is_loopback
            ]
        xknx = XKNX()
        found: set[tuple[str, int]] = set()
        errors: list[str] = []
        await asyncio.gather(
            *(
                self._scan_interface(
                    xknx,
                    local_ip=local_ip,
                    timeout=args.timeout,
                    found=found,
                    errors=errors,
                    ignore_errors=args.local_ip is None,
                )
                for local_ip in dict.fromkeys(local_ips)
            )
        )
        if not found:
            for failure in errors:
                print(f"Scan failed on {failure}", file=sys.stderr)
            print("No gateways found.", file=sys.stderr)
            return 1
        return 0

    async def _scan_interface(
        self,
        xknx: XKNX,
        local_ip: str,
        timeout: float,
        found: set[tuple[str, int]],
        errors: list[str],
        ignore_errors: bool,
    ) -> None:
        """Scan for gateways on a single interface."""
        gatewayscanner = GatewayScanner(
            xknx, local_ip=local_ip, timeout_in_seconds=timeout
        )
        try:
            async for gateway in gatewayscanner.async_scan():
                key = (gateway.ip_addr, gateway.port)
                if key in found:
                    continue
                found.add(key)
                _print_gateway(gateway)
        except (XKNXException, OSError) as err:
            if not ignore_errors:
                raise
            errors.append(f"{local_ip}: {err}")
            logger.debug("Scan failed on %s: %s", local_ip, err)
