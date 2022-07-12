"""
Module for serialization and deserialization of KNX HPAI (Host Protocol Address Information) information.

A HPAI contains an IP address and a port.
"""
from __future__ import annotations

import socket

from xknx.exceptions import ConversionError, CouldNotParseKNXIP

from .knxip_enum import HostProtocol


class HPAI:
    """Class for Module for Serialization and Deserialization."""

    LENGTH = 0x08

    def __init__(
        self,
        ip_addr: str = "0.0.0.0",
        port: int = 0,
        protocol: HostProtocol = HostProtocol.IPV4_UDP,
    ) -> None:
        """Initialize HPAI object."""
        self.ip_addr = ip_addr
        self.port = port
        self.protocol = protocol

    @property
    def route_back(self) -> bool:
        """Return True if HPAI is a route back address information."""
        return self.ip_addr == "0.0.0.0"

    @property
    def addr_tuple(self) -> tuple[str, int]:
        """Return tuple of ip address and port."""
        return self.ip_addr, self.port

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < HPAI.LENGTH:
            raise CouldNotParseKNXIP("wrong HPAI length")
        if raw[0] != HPAI.LENGTH:
            raise CouldNotParseKNXIP("wrong HPAI length")
        try:
            self.protocol = HostProtocol(raw[1])
        except ValueError as err:
            raise CouldNotParseKNXIP("unsupported host protocol code") from err
        self.ip_addr = socket.inet_ntoa(raw[2:6])
        self.port = raw[6] * 256 + raw[7]
        return HPAI.LENGTH

    def to_knx(self) -> bytes:
        """Serialize to KNX/IP raw data."""
        try:
            return (
                bytes((HPAI.LENGTH, self.protocol.value))
                + socket.inet_aton(self.ip_addr)
                + self.port.to_bytes(2, "big")
            )
        except (OSError, TypeError) as err:
            # OSError for invalid address strings; TypeError for non-strings
            raise ConversionError(f"Invalid IPv4 address: {self.ip_addr}") from err
        except (OverflowError, AttributeError) as err:
            # OverflowError for int < 0 or int > 65535; AttributeError for non-integers
            raise ConversionError(f"Port is not valid: {self.port}") from err

    def __repr__(self) -> str:
        """Representation of object."""
        return f"HPAI('{self.ip_addr}', {self.port}, {self.protocol})"

    def __str__(self) -> str:
        """Return object as readable string."""
        return f"{self.ip_addr}:{self.port}/{self.protocol.name[-3:].lower()}"

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hash function."""
        return hash((self.ip_addr, self.port, self.protocol))
