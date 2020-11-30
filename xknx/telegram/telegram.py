"""
Module for KNX Telegrams.

The telegram class is the leightweight interaction object between

* business logic (Lights, Covers, etc) and
* underlaying KNX/IP abstraction (KNX-Routing/KNX-Tunneling).

It contains

* the telegram type (e.g. GROUP_WRITE)
* the direction (incoming or outgoing)
* the group address (e.g. 1/2/3)
* and the payload (e.g. "12%" or "23.23 C".

"""
from enum import Enum
from typing import Any, Union

from .address import GroupAddress, IndividualAddress


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = "Incoming"
    OUTGOING = "Outgoing"


class TelegramType(Enum):
    """Enum class for type of telegram."""

    GROUP_READ = "GroupValueRead"
    GROUP_WRITE = "GroupValueWrite"
    GROUP_RESPONSE = "GroupValueResponse"


class Telegram:
    """Class for KNX telegrams."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        destination_address: Union[GroupAddress, IndividualAddress] = GroupAddress(
            None
        ),
        telegramtype: TelegramType = TelegramType.GROUP_WRITE,
        direction: TelegramDirection = TelegramDirection.OUTGOING,
        payload: Any = None,
        source_address: IndividualAddress = IndividualAddress(None),
    ) -> None:
        """Initialize Telegram class."""
        self.destination_address = destination_address
        self.telegramtype = telegramtype
        self.direction = direction
        self.payload = payload
        self.source_address = source_address

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<Telegram direction="{}" telegramtype="{}" source_address="{}" '
            'destination_address="{}" payload="{}" />'.format(
                self.direction.value,
                self.telegramtype.value,
                self.source_address,
                self.destination_address,
                self.payload,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return bool(self.__dict__ == other.__dict__)

    def __hash__(self) -> int:
        """Hash function."""
        # used to turn lists of Telegram into sets in unittests
        return hash(str(self))
