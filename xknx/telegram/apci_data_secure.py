"""Class for APCI payloads used in KNX Data Secure."""
from __future__ import annotations

from enum import IntEnum


class SecurityAlgorithmIdentifier(IntEnum):
    """Enum representing the used security algorithm."""

    CCM_AUTHENTICATION = 0b000
    CCM_ENCRYPTION = 0b001


class SecurityALService(IntEnum):
    """Enum representing the used security application layer service."""

    S_A_DATA = 0b000
    S_A_SYNC_REQ = 0b001
    S_A_SYNC_RES = 0b011


class SecurityControlFiled:
    """Class for KNX Data Secure Security Control Field (SCF)."""

    def __init__(
        self,
        tool_access: bool,
        algorithm: SecurityAlgorithmIdentifier,
        system_broadcast: bool,
        service: SecurityALService,
    ) -> None:
        """Initialize SecurityControlFiled class."""
        self.tool_access = tool_access
        self.algorithm = algorithm
        self.system_broadcast = system_broadcast
        self.service = service

    @staticmethod
    def from_knx(raw: int) -> SecurityControlFiled:
        """Parse/deserialize from KNX raw data."""
        tool_access = bool(raw & 0b10000000)
        sai = SecurityAlgorithmIdentifier(raw >> 4 & 0b111)
        system_broadcast = bool(raw & 0b1000)
        s_al_service = SecurityALService(raw & 0b111)

        return SecurityControlFiled(
            tool_access=tool_access,
            algorithm=sai,
            system_broadcast=system_broadcast,
            service=s_al_service,
        )

    def to_knx(self) -> bytes:
        """Serialize to KNX raw data."""
        raw = 0
        raw |= self.tool_access << 7
        raw |= self.algorithm << 4
        raw |= self.system_broadcast << 3
        raw |= self.service
        return raw.to_bytes(1, "big")

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<SecurityControlFiled tool_access="{self.tool_access}" '
            f'algorithm="{self.algorithm}" '
            f'system_broadcast="{self.system_broadcast}" '
            f'service="{self.service}" />'
        )
