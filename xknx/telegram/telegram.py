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
from typing import Any

from .address import GroupAddress


class TelegramDirection(Enum):
    """Enum class for the communication direction of a telegram (from KNX bus or to KNX bus)."""

    INCOMING = 1
    OUTGOING = 2


class TelegramType(Enum):
    """Enum class for type of telegram."""

    GROUP_READ = 1
    GROUP_WRITE = 2
    GROUP_RESPONSE = 3


class Telegram:
    """Class for KNX telegrams."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        group_address: GroupAddress = GroupAddress(None),
        telegramtype: TelegramType = TelegramType.GROUP_WRITE,
        direction: TelegramDirection = TelegramDirection.OUTGOING,
        payload: Any = None,
    ) -> None:
        """Initialize Telegram class."""
        self.direction = direction
        self.telegramtype = telegramtype
        self.group_address = group_address
        self.payload = payload

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            '<Telegram group_address="{}", payload="{}" '
            'telegramtype="{}" direction="{}" />'.format(
                self.group_address.__repr__(),
                self.payload,
                self.telegramtype,
                self.direction,
            )
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        return bool(self.__dict__ == other.__dict__)

    def __hash__(self) -> int:
        """Hash function."""
        # used to turn lists of Telegram into sets in unittests
        return hash(str(self))
