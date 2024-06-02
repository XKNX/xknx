"""
Module for KNX Telegrams.

The telegram class is the lightweight data transfer object between

* business logic (Lights, Covers, etc) and
* underlying KNX/IP abstraction (CEMIHandler).

It contains

* the group address (e.g. GroupAddress("1/2/3"))
* the direction (Incoming or Outgoing)
* and the payload (e.g. GroupValueWrite(DPTBinary(False)))
* the source address (e.g. IndividualAddress("1.2.3"))
* the TPCI (Transport Layer Control Information) (e.g. TDataGroup())
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .address import GroupAddress, IndividualAddress, InternalGroupAddress
from .apci import APCI
from .tpci import TPCI, TDataBroadcast, TDataGroup, TDataIndividual


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


@dataclass(slots=True)
class Telegram:
    """Class for KNX telegrams."""

    destination_address: GroupAddress | IndividualAddress | InternalGroupAddress
    direction: TelegramDirection = TelegramDirection.OUTGOING
    payload: APCI | None = None
    source_address: IndividualAddress = field(
        default_factory=lambda: IndividualAddress(0)
    )
    tpci: TPCI = None  # type: ignore[assignment]  # set in __post_init__

    def __post_init__(self) -> None:
        """Initialize Telegram class."""
        if self.tpci is None:
            if isinstance(self.destination_address, GroupAddress):  # type: ignore[unreachable]
                if self.destination_address.raw == 0:
                    self.tpci = TDataBroadcast()
                else:
                    self.tpci = TDataGroup()
            elif isinstance(self.destination_address, IndividualAddress):
                self.tpci = TDataIndividual()
            else:  # InternalGroupAddress
                self.tpci = TDataGroup()

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
