"""
Module for serialization and deserialization of KNX HPAI (Host Protocol Address Information) information.

A HPAI contains an IP address and a port.
"""
from __future__ import annotations

from typing import Iterator

from xknx.exceptions import ConversionError, CouldNotParseKNXIP


class HPAI:
    """Class for Module for Serialization and Deserialization."""

    LENGTH = 0x08
    TYPE_UDP = 0x01

    def __init__(self, ip_addr: str = "0.0.0.0", port: int = 0):
        """Initialize HPAI object."""
        self.ip_addr = ip_addr
        self.port = port

    def from_knx(self, raw: bytes) -> int:
        """Parse/deserialize from KNX/IP raw data."""
        if len(raw) < HPAI.LENGTH:
            raise CouldNotParseKNXIP("wrong HPAI length")
        if raw[0] != HPAI.LENGTH:
            raise CouldNotParseKNXIP("wrong HPAI length")
        if raw[1] != HPAI.TYPE_UDP:
            raise CouldNotParseKNXIP("wrong HPAI type")
        self.ip_addr = f"{raw[2]}.{raw[3]}.{raw[4]}.{raw[5]}"
        self.port = raw[6] * 256 + raw[7]
        return HPAI.LENGTH

    def to_knx(self) -> list[int]:
        """Serialize to KNX/IP raw data."""

        def ip_addr_to_bytes(ip_addr: str) -> Iterator[int]:
            """Serialize ip address to byte array."""
            if not isinstance(ip_addr, str):
                raise ConversionError("ip_addr is not a string")
            for i in ip_addr.split("."):
                yield int(i)

        data = []
        data.append(HPAI.LENGTH)
        data.append(HPAI.TYPE_UDP)
        data.extend(ip_addr_to_bytes(self.ip_addr))
        data.append((self.port >> 8) & 255)
        data.append(self.port & 255)
        return data

    def __repr__(self) -> str:
        """Representation of object."""
        return f"HPAI('{self.ip_addr}', {self.port})"

    def __str__(self) -> str:
        """Return object as readable string."""
        return f"{self.ip_addr}:{self.port}"

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__
