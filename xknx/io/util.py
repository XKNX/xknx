"""Helper functions for XKNX io module."""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import socket
from typing import cast

import ifaddr

from xknx.exceptions import XKNXException

from .const import DEFAULT_MCAST_GRP, DEFAULT_MCAST_PORT

logger = logging.getLogger("xknx.log")


async def get_default_local_ip(remote_ip: str = DEFAULT_MCAST_GRP) -> str | None:
    """Return the local ip used for communication with remote_ip."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setblocking(False)  # must be non-blocking for async
        loop = asyncio.get_running_loop()
        try:
            await loop.sock_connect(sock, (remote_ip, DEFAULT_MCAST_PORT))
            local_ip = sock.getsockname()[0]
            logger.debug("Using local ip: %s", local_ip)
            return local_ip  # type: ignore[no-any-return]
        except Exception:  # pylint: disable=broad-except
            logger.warning(
                "The system could not auto detect the source ip for %s on your operating system",
                remote_ip,
            )
            return None


def get_local_ips() -> list[ifaddr.IP]:
    """Return list of local IPv4 addresses."""
    return [ip for iface in ifaddr.get_adapters() for ip in iface.ips if ip.is_IPv4]


def get_local_interface_name(local_ip: str) -> str:
    """Return the name of the interface with the given ip."""
    return next((link.nice_name for link in get_local_ips() if link.ip == local_ip), "")


def get_ip_for_adapter_name(name: str) -> str | None:
    """Return the ip for the given interface name."""
    return next(
        (
            ip.ip  # type: ignore[misc] # IPv6 would return tuple
            for iface in ifaddr.get_adapters()
            if name in (iface.name, iface.nice_name)
            for ip in iface.ips
            if ip.is_IPv4
        ),
        None,
    )


def find_local_ip(gateway_ip: str) -> str | None:
    """Find local IP address on same subnet as gateway."""
    gateway = ipaddress.IPv4Address(gateway_ip)
    for link in get_local_ips():
        network = ipaddress.IPv4Network((link.ip, link.network_prefix), strict=False)
        if gateway in network:
            logger.debug("Using interface: %s", link.nice_name)
            return cast(str, link.ip)
    logger.debug("No interface on same subnet as gateway found.")
    return None


async def validate_ip(address: str, address_name: str = "IP address") -> str:
    """
    Return IPv4 address parsed or resolved as a string.

    Valid addresses are IPv4 strings, adapter names or hostnames.
    Raises XKNXException if address is not a valid IPv4 address or cannot be resolved.
    """
    try:
        ipaddress.IPv4Address(address)
        return address
    except ipaddress.AddressValueError as ex:
        logger.debug(
            "%s is not a valid IPv4 address: %s. Trying to resolve...",
            address_name,
            ex,
        )
    if adapter_ip := get_ip_for_adapter_name(address):
        return adapter_ip
    try:
        return await asyncio.to_thread(socket.gethostbyname, address)
    except socket.gaierror as ex:
        raise XKNXException(f"Could not resolve {address_name}: {address}") from ex
