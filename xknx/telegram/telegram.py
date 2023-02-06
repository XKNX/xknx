"""
Module for KNX Telegrams.

The telegram class is the lightweight interaction object between

* business logic (Lights, Covers, etc) and
* underlying KNX/IP abstraction (KNX-Routing/KNX-Tunneling).

It contains

* the direction (incoming or outgoing)
* the group address (e.g. 1/2/3)
* and the payload (e.g. GroupValueWrite("12%")).

"""
from __future__ import annotations

from enum import Enum

from .address import GroupAddress, IndividualAddress, InternalGroupAddress
from .apci import APCI
from .tpci import TPCI, TDataBroadcast, TDataGroup, TDataIndividual


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


class Telegram:
    """Class for KNX telegrams."""

    def __init__(
        self,
        destination_address: GroupAddress | IndividualAddress | InternalGroupAddress,
        direction: TelegramDirection = TelegramDirection.OUTGOING,
        payload: APCI | None = None,
        source_address: IndividualAddress | None = None,
        tpci: TPCI | None = None,
    ) -> None:
        """Initialize Telegram class."""
        self.destination_address = destination_address
        self.direction = direction
        self.payload = payload
        self.source_address = source_address or IndividualAddress(0)
        self.tpci: TPCI
        if tpci is None:
            if isinstance(destination_address, GroupAddress):
                if destination_address.raw == 0:
                    self.tpci = TDataBroadcast()
                else:
                    self.tpci = TDataGroup()
            elif isinstance(destination_address, IndividualAddress):
                self.tpci = TDataIndividual()
            else:  # InternalGroupAddress
                self.tpci = TDataGroup()
        else:
            self.tpci = tpci

    def __str__(self) -> str:
        """Return object as readable string."""
        data = f'payload="{self.payload}"' if self.payload else f'tpci="{self.tpci}"'
        return (
            "<Telegram "
            f'direction="{self.direction.value}" '
            f'source_address="{self.source_address}" '
            f'destination_address="{self.destination_address}" '
            f"{data} />"
        )

    def __repr__(self) -> str:
        """Return object as string representation."""
        return (
            "Telegram("
            f"destination_address={self.destination_address}, "
            f"direction={self.direction}, "
            f"payload={self.payload}, "
            f"source_address={self.source_address}, "
            f"tpci={self.tpci}"
            ")"
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Hash function."""
        # used to turn lists of Telegram into sets in unittests
        return hash(repr(self))
