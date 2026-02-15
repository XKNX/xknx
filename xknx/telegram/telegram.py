"""Module for KNX Telegrams."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from xknx.dpt import DPTBase, DPTComplexData, DPTEnumData

from .address import GroupAddress, IndividualAddress, InternalGroupAddress
from .apci import APCI
from .tpci import TPCI, TDataBroadcast, TDataGroup, TDataIndividual


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


@dataclass(slots=True)
class TelegramDecodedData:
    """Context for a telegram."""

    transcoder: type[DPTBase]
    value: bool | int | float | str | DPTComplexData | DPTEnumData

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f"{self.value}{' ' + self.transcoder.unit if self.transcoder.unit is not None else ''}"
            f" ({self.transcoder.dpt_name()})"
        )


@dataclass(slots=True)
class Telegram:
    """
    Data transfer object for KNX telegrams.

    Represents a message exchanged on the KNX bus between the business logic
    (Devices, Management, etc.) and the underlying KNX/IP abstraction layer.

    Attributes:
        destination_address: Target GroupAddress, IndividualAddress, or
            InternalGroupAddress.
        direction: Communication direction (INCOMING or OUTGOING).
        payload: APCi payload containing the actual data (e.g., GroupValueWrite,
            GroupValueResponse). None for control information only telegrams.
        source_address: IndividualAddress of the sender. When default of 0.0.0 is
            used, it will be set automatically when sent.
        tpci: Transport Layer Control Information (TDataBroadcast, TDataGroup, or
            TDataIndividual). If not provided, it will be automatically inferred
            based on destination_address type.
        decoded_data: Optional decoded version of the payload including the
            transcoder class and decoded value. Set externally by GroupAddressDPT
            for convenience when the payload has already been decoded.
        data_secure: Flag indicating if the telegram was sent or received as
            DataSecure. Set externally by CEMIHandler. None if not yet processed.

    """

    destination_address: GroupAddress | IndividualAddress | InternalGroupAddress
    direction: TelegramDirection = TelegramDirection.OUTGOING
    payload: APCI | None = None
    source_address: IndividualAddress = field(
        default_factory=lambda: IndividualAddress(0)
    )
    tpci: TPCI = None  # type: ignore[assignment]  # set by initializer or in __post_init__
    # set by GroupAddressDPT
    decoded_data: TelegramDecodedData | None = field(
        init=False, default=None, compare=False, hash=False
    )
    # flag if telegram was sent or received as DataSecure, set by CEMIHandler
    data_secure: bool | None = field(
        init=False, default=None, compare=False, hash=False
    )

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
        decoded_data = (
            f' data="{self.decoded_data}"' if self.decoded_data is not None else ""
        )
        return (
            "<Telegram "
            f'direction="{self.direction.value}" '
            f'source_address="{self.source_address}" '
            f'destination_address="{self.destination_address}" '
            f"{data}{decoded_data} />"
        )
