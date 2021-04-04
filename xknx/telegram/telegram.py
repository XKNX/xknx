"""
Module for KNX Telegrams.

The telegram class is the leightweight interaction object between

* business logic (Lights, Covers, etc) and
* underlaying KNX/IP abstraction (KNX-Routing/KNX-Tunneling).

It contains

* the direction (incoming or outgoing)
* the group address (e.g. 1/2/3)
* and the payload (e.g. GroupValueWrite("12%")).

"""
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from .address import GroupAddress, IndividualAddress
from .apci import APCI


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


class Telegram:
    """Class for KNX telegrams."""

    def __init__(
        self,
        destination_address: Union[GroupAddress, IndividualAddress] = GroupAddress(0),
        direction: TelegramDirection = TelegramDirection.OUTGOING,
        payload: Optional[APCI] = None,
        source_address: IndividualAddress = IndividualAddress(0),
    ) -> None:
        """Initialize Telegram class."""
        self.destination_address = destination_address
        self.direction = direction
        self.payload = payload
        self.source_address = source_address
        self.reception_time = datetime.now()

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<Telegram direction="{}" source_address="{}" '
            'destination_address="{}" payload="{}" />'.format(
                self.direction.value,
                self.source_address,
                self.destination_address,
                self.payload,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        for key, value in self.__dict__.items():
            if key == "reception_time":
                continue
            if key not in other.__dict__:
                return False
            if other.__dict__[key] != value:
                return False
        for key, value in other.__dict__.items():
            if key not in self.__dict__:
                return False
        return True

    def __hash__(self) -> int:
        """Hash function."""
        # used to turn lists of Telegram into sets in unittests
        return hash(str(self))
