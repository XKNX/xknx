"""Helper functions for XKNX."""
from __future__ import annotations

import ipaddress
import logging
from typing import cast

import netifaces

from xknx.exceptions import CommunicationError, XKNXException

logger = logging.getLogger("xknx.log")


def find_local_ip(gateway_ip: str) -> str:
    """Find local IP address on same subnet as gateway."""

    def _scan_interfaces(gateway: ipaddress.IPv4Address) -> str | None:
        """Return local IP address on same subnet as given gateway."""
        for interface in netifaces.interfaces():
            try:
                af_inet = netifaces.ifaddresses(interface)[netifaces.AF_INET]
                for link in af_inet:
                    network = ipaddress.IPv4Network(
                        (link["addr"], link["netmask"]), strict=False
                    )
                    if gateway in network:
                        logger.debug("Using interface: %s", interface)
                        return cast(str, link["addr"])
            except KeyError:
                logger.debug("Could not find IPv4 address on interface %s", interface)
                continue
        return None

    def _find_default_gateway() -> ipaddress.IPv4Address:
        """Return IP address of default gateway."""
        gws = netifaces.gateways()
        return ipaddress.IPv4Address(gws["default"][netifaces.AF_INET][0])

    gateway = ipaddress.IPv4Address(gateway_ip)
    local_ip = _scan_interfaces(gateway)
    if local_ip is None:
        logger.warning(
            "No interface on same subnet as gateway found. Falling back to default gateway."
        )
        try:
            default_gateway = _find_default_gateway()
        except KeyError as err:
            raise CommunicationError(f"No route to {gateway} found") from err
        local_ip = _scan_interfaces(default_gateway)
    assert isinstance(local_ip, str)
    return local_ip


def validate_ip(address: str, address_name: str = "IP address") -> None:
    """Raise an exception if address cannot be parsed as IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError as ex:
        raise XKNXException(f"{address_name} is not a valid IPv4 address.") from ex
